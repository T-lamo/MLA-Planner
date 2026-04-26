"""Routes API pour les templates de planning."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import (
    CapabilityChecker,
    RoleChecker,
    get_current_active_user,
)
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import DataResponse, Utilisateur
from models.base_pagination import PaginatedResponse
from models.planning_template_model import (
    ApplyTemplateResultSchema,
    PlanningTemplateCreate,
    PlanningTemplateFullUpdate,
    PlanningTemplateListItem,
    PlanningTemplateRead,
    PlanningTemplateUpdate,
    SaveAsTemplateRequest,
)
from models.serie_model import (
    GenerateSeriesPreviewRequest,
    GenerateSeriesRequest,
    GenerateSeriesResponse,
    SeriesPreviewResponse,
)
from services.planning_template_service import PlanningTemplateSvc
from services.serie_service import SerieService

router = APIRouter(
    prefix="/planning-templates",
    tags=["PlanningTemplates"],
)

_WRITE_ROLES = RoleChecker(["RESPONSABLE_MLA", "ADMIN", "Super Admin"])
# Lecture : tout utilisateur avec TEMPLATE_READ ou TEMPLATE_WRITE
_READ_CHECK = CapabilityChecker(["TEMPLATE_READ", "TEMPLATE_WRITE"])


def _get_svc(db: Session = Depends(Database.get_db_for_route)) -> PlanningTemplateSvc:
    """Factory d'injection du service template."""
    return PlanningTemplateSvc(db)


def _get_serie_svc(
    db: Session = Depends(Database.get_db_for_route),
) -> SerieService:
    """Factory d'injection du service série."""
    return SerieService(db)


def _resolve_ministere_id(user: Utilisateur) -> Optional[str]:
    """Extrait le premier ministère du membre courant, ou None pour les admins."""
    membre = user.membre
    if membre and membre.ministeres:
        return str(membre.ministeres[0].id)
    return None


def _resolve_ministere_campus(user: Utilisateur) -> tuple[str, str]:
    """Retourne (ministere_id, campus_id) depuis le membre courant."""
    membre = user.membre
    if not membre:
        raise AppException(ErrorRegistry.TMPL_005)
    ministere_id = str(membre.ministeres[0].id) if membre.ministeres else None
    campus_id = membre.campus_principal_id
    if not ministere_id or not campus_id:
        raise AppException(ErrorRegistry.TMPL_005)
    return ministere_id, campus_id


@router.post(
    "/preview-series",
    response_model=SeriesPreviewResponse,
    status_code=200,
    summary="Prévisualiser les dates d'une série",
    dependencies=[Depends(_WRITE_ROLES)],
)
def preview_series(
    payload: GenerateSeriesPreviewRequest,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: SerieService = Depends(_get_serie_svc),
) -> SeriesPreviewResponse:
    """Calcule les dates selon la récurrence et détecte les conflits."""
    ministere_id = _resolve_ministere_id(current_user)
    return svc.get_series_preview(payload, ministere_id=ministere_id)


@router.post(
    "/generate-series",
    response_model=GenerateSeriesResponse,
    status_code=201,
    summary="Générer une série de plannings depuis un template",
    dependencies=[Depends(_WRITE_ROLES)],
)
def generate_series(
    payload: GenerateSeriesRequest,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: SerieService = Depends(_get_serie_svc),
) -> GenerateSeriesResponse:
    """Crée N plannings en BROUILLON depuis un template avec un serie_id commun."""
    ministere_id, campus_id = _resolve_ministere_campus(current_user)
    created_by_id = str(current_user.membre_id or "")
    return svc.generate_series(
        payload,
        created_by_id=created_by_id,
        ministere_id=ministere_id,
        campus_id=campus_id,
    )


@router.post(
    "/from-planning/{planning_id}",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
    status_code=201,
)
def save_planning_as_template(
    planning_id: str,
    body: SaveAsTemplateRequest,
    db: Session = Depends(Database.get_db_for_route),
    current_user: Utilisateur = Depends(get_current_active_user),
) -> DataResponse[PlanningTemplateRead]:
    """Sauvegarde un planning existant comme template réutilisable."""
    svc = PlanningTemplateSvc(db)
    result = svc.save_planning_as_template(
        planning_id, body, current_user.membre_id or ""
    )
    return DataResponse(data=result)


@router.get(
    "/by-campus/{campus_id}",
    response_model=PaginatedResponse[PlanningTemplateRead],
    dependencies=[Depends(_READ_CHECK)],
)
def list_templates_by_campus(
    campus_id: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(Database.get_db_for_route),
) -> PaginatedResponse[PlanningTemplateRead]:
    """Liste paginée des templates d'un campus."""
    svc = PlanningTemplateSvc(db)
    items = svc.list_by_campus(campus_id)
    total = len(items)
    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        data=items[offset : offset + limit],
    )


@router.get(
    "/by-ministere/{ministere_id}",
    response_model=PaginatedResponse[PlanningTemplateRead],
    dependencies=[Depends(_READ_CHECK)],
)
def list_templates_by_ministere(
    ministere_id: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(Database.get_db_for_route),
) -> PaginatedResponse[PlanningTemplateRead]:
    """Liste paginée des templates d'un ministère."""
    svc = PlanningTemplateSvc(db)
    items = svc.list_by_ministere(ministere_id)
    total = len(items)
    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        data=items[offset : offset + limit],
    )


@router.post(
    "",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
    status_code=201,
)
def create_template(
    body: PlanningTemplateCreate,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> DataResponse[PlanningTemplateRead]:
    """Crée un template vierge depuis la bibliothèque."""
    return DataResponse(data=svc.create_template(body, current_user))


@router.get(
    "",
    response_model=PaginatedResponse[PlanningTemplateListItem],
    dependencies=[Depends(_READ_CHECK)],
)
def list_templates(
    ministere_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> PaginatedResponse[PlanningTemplateListItem]:
    """Liste paginée des templates — bibliothèque US-95."""
    items = svc.list_templates(current_user, ministere_id)
    total = len(items)
    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        data=items[offset : offset + limit],
    )


@router.get(
    "/{template_id}",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_READ_CHECK)],
)
def get_template(
    template_id: str,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> DataResponse[PlanningTemplateRead]:
    """Récupère un template par son identifiant."""
    return DataResponse(data=svc.get_template_full(template_id, current_user))


@router.put(
    "/{template_id}",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
)
def update_template_full(
    template_id: str,
    body: PlanningTemplateFullUpdate,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> DataResponse[PlanningTemplateRead]:
    """Remplace complètement nom, description et créneaux du template."""
    return DataResponse(data=svc.update_template_full(template_id, body, current_user))


@router.patch(
    "/{template_id}",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
)
def update_template(
    template_id: str,
    body: PlanningTemplateUpdate,
    db: Session = Depends(Database.get_db_for_route),
) -> DataResponse[PlanningTemplateRead]:
    """Met à jour le nom ou la description d'un template."""
    svc = PlanningTemplateSvc(db)
    return DataResponse(data=svc.update_template(template_id, body))


@router.post(
    "/{template_id}/duplicate",
    response_model=DataResponse[PlanningTemplateListItem],
    dependencies=[Depends(_WRITE_ROLES)],
    status_code=201,
)
def duplicate_template(
    template_id: str,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> DataResponse[PlanningTemplateListItem]:
    """Duplique un template existant."""
    copy = svc.duplicate_template(template_id, current_user)
    return DataResponse(data=copy)


@router.delete(
    "/{template_id}",
    status_code=204,
    dependencies=[Depends(_WRITE_ROLES)],
)
def delete_template(
    template_id: str,
    current_user: Utilisateur = Depends(get_current_active_user),
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> None:
    """Supprime un template (nullifie les refs dans les plannings)."""
    svc.delete_template_with_access(template_id, current_user)


@router.post(
    "/{template_id}/apply/{planning_id}",
    response_model=ApplyTemplateResultSchema,
    dependencies=[Depends(_WRITE_ROLES)],
    status_code=200,
)
def apply_template(
    template_id: str,
    planning_id: str,
    svc: PlanningTemplateSvc = Depends(_get_svc),
) -> ApplyTemplateResultSchema:
    """Applique un template sur un planning existant (US-96).

    Crée des slots et des affectations PROPOSE pour chaque membre suggéré
    éligible. Retourne les avertissements d'indisponibilité et membres ignorés.
    """
    result = svc.apply_to_planning(template_id, planning_id)
    return ApplyTemplateResultSchema(**result)
