"""Routes API pour les templates de planning."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker, get_current_active_user
from models import DataListResponse, DataResponse, Utilisateur
from models.planning_template_model import (
    PlanningTemplateRead,
    PlanningTemplateUpdate,
    SaveAsTemplateRequest,
)
from services.planning_template_service import PlanningTemplateSvc

router = APIRouter(
    prefix="/planning-templates",
    tags=["PlanningTemplates"],
)

_WRITE_ROLES = RoleChecker(["RESPONSABLE_MLA", "ADMIN", "Super Admin"])


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
    response_model=DataListResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
)
def list_templates_by_campus(
    campus_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> DataListResponse[PlanningTemplateRead]:
    """Liste les templates d'un campus, triés par fréquence d'usage."""
    svc = PlanningTemplateSvc(db)
    items = svc.list_by_campus(campus_id)
    return DataListResponse(data=items)


@router.get(
    "/by-ministere/{ministere_id}",
    response_model=DataListResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
)
def list_templates_by_ministere(
    ministere_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> DataListResponse[PlanningTemplateRead]:
    """Liste les templates d'un ministère, triés par fréquence d'usage."""
    svc = PlanningTemplateSvc(db)
    items = svc.list_by_ministere(ministere_id)
    return DataListResponse(data=items)


@router.get(
    "/{template_id}",
    response_model=DataResponse[PlanningTemplateRead],
    dependencies=[Depends(_WRITE_ROLES)],
)
def get_template(
    template_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> DataResponse[PlanningTemplateRead]:
    """Récupère un template par son identifiant."""
    svc = PlanningTemplateSvc(db)
    return DataResponse(data=svc.get_template(template_id))


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


@router.delete(
    "/{template_id}",
    status_code=204,
    dependencies=[Depends(_WRITE_ROLES)],
)
def delete_template(
    template_id: str,
    db: Session = Depends(Database.get_db_for_route),
) -> None:
    """Supprime un template (cascade sur créneaux et rôles)."""
    PlanningTemplateSvc(db).delete_template(template_id)
