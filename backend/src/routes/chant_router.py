"""
Router du module Songbook.

Préfixe : /chants
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker, get_current_active_user
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import RoleName
from models import Utilisateur
from models.base_pagination import PaginatedResponse
from models.chant_model import (
    ChantCategorieCreate,
    ChantCategorieRead,
    ChantCategorieUpdate,
    ChantContenuCreate,
    ChantContenuRead,
    ChantContenuUpdate,
    ChantCreate,
    ChantRead,
    ChantReadFull,
    ChantTransposeRequest,
    ChantTransposeResponse,
    ChantUpdate,
)
from services.chant_service import ChantCategorieService, ChantService

router = APIRouter(prefix="/chants", tags=["Songbook"])

_DB = Depends(Database.get_db_for_route)
_AUTH = Depends(RoleChecker(["Super Admin", "Admin", "RESPONSABLE_MLA", "MEMBRE_MLA"]))
_ADMIN = Depends(RoleChecker(["Super Admin", "Admin", "RESPONSABLE_MLA"]))


def _get_cat_svc(db: Session = _DB) -> ChantCategorieService:  # type: ignore
    return ChantCategorieService(db)


def _get_svc(db: Session = _DB) -> ChantService:  # type: ignore
    return ChantService(db)


# ------------------------------------------------------------------ #
#  CATÉGORIES
# ------------------------------------------------------------------ #


@router.get(
    "/categories",
    response_model=List[ChantCategorieRead],
    status_code=status.HTTP_200_OK,
    summary="Lister les catégories de chants",
    dependencies=[_AUTH],
)
def list_categories(
    svc: ChantCategorieService = Depends(_get_cat_svc),
) -> List[ChantCategorieRead]:
    cats = svc.list_categories()
    return [ChantCategorieRead.model_validate(c) for c in cats]


@router.post(
    "/categories",
    response_model=ChantCategorieRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une catégorie de chant",
    dependencies=[_ADMIN],
)
def create_categorie(
    payload: ChantCategorieCreate,
    svc: ChantCategorieService = Depends(_get_cat_svc),
) -> ChantCategorieRead:
    cat = svc.create_categorie(payload)
    return ChantCategorieRead.model_validate(cat)


@router.patch(
    "/categories/{code}",
    response_model=ChantCategorieRead,
    status_code=status.HTTP_200_OK,
    summary="Mettre à jour une catégorie",
    dependencies=[_ADMIN],
)
def update_categorie(
    code: str,
    payload: ChantCategorieUpdate,
    svc: ChantCategorieService = Depends(_get_cat_svc),
) -> ChantCategorieRead:
    cat = svc.update_categorie(code, payload)
    return ChantCategorieRead.model_validate(cat)


@router.delete(
    "/categories/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une catégorie vide",
    dependencies=[_ADMIN],
)
def delete_categorie(
    code: str,
    svc: ChantCategorieService = Depends(_get_cat_svc),
) -> None:
    svc.delete_categorie(code)


# ------------------------------------------------------------------ #
#  CHANTS
# ------------------------------------------------------------------ #


_ADMIN_ROLES = {RoleName.SUPER_ADMIN, RoleName.ADMIN}


@router.get(
    "",
    response_model=PaginatedResponse[ChantRead],
    status_code=status.HTTP_200_OK,
    summary="Lister les chants (paginé, multi-tenant)",
)
def list_chants(  # pylint: disable=too-many-positional-arguments
    campus_id: Optional[str] = Query(None, description="Filtre multi-tenant"),
    categorie_code: Optional[str] = Query(None),
    artiste: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Recherche sur le titre"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: ChantService = Depends(_get_svc),
    current_user: Utilisateur = Depends(get_current_active_user),
) -> PaginatedResponse[ChantRead]:
    if campus_id is None:
        user_roles = {
            aff.role.libelle
            for aff in current_user.affectations
            if aff.role and aff.role.libelle is not None
        }
        if not user_roles.intersection(_ADMIN_ROLES):
            raise AppException(ErrorRegistry.SONG_008)
    items, total = svc.list_chants(
        campus_id=campus_id,
        categorie_code=categorie_code,
        artiste=artiste,
        q=q,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(total=total, limit=limit, offset=offset, data=items)


@router.post(
    "",
    response_model=ChantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un chant",
    dependencies=[_ADMIN],
)
def create_chant(
    payload: ChantCreate,
    svc: ChantService = Depends(_get_svc),
) -> ChantRead:
    return svc.create_chant(payload)


@router.get(
    "/{chant_id}",
    response_model=ChantReadFull,
    status_code=status.HTTP_200_OK,
    summary="Détail d'un chant (avec contenu et catégorie)",
    dependencies=[_AUTH],
)
def get_chant(
    chant_id: str,
    svc: ChantService = Depends(_get_svc),
) -> ChantReadFull:
    return svc.get_chant_full(chant_id)


@router.patch(
    "/{chant_id}",
    response_model=ChantRead,
    status_code=status.HTTP_200_OK,
    summary="Mettre à jour un chant",
    dependencies=[_ADMIN],
)
def update_chant(
    chant_id: str,
    payload: ChantUpdate,
    svc: ChantService = Depends(_get_svc),
) -> ChantRead:
    return svc.update_chant(chant_id, payload)


@router.delete(
    "/{chant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un chant (soft delete)",
    dependencies=[_ADMIN],
)
def delete_chant(
    chant_id: str,
    svc: ChantService = Depends(_get_svc),
) -> None:
    svc.delete_chant(chant_id)


# ------------------------------------------------------------------ #
#  CONTENU CHORDPRO
# ------------------------------------------------------------------ #


@router.get(
    "/{chant_id}/contenu",
    response_model=ChantContenuRead,
    status_code=status.HTTP_200_OK,
    summary="Récupérer le contenu ChordPro",
    dependencies=[_AUTH],
)
def get_contenu(
    chant_id: str,
    svc: ChantService = Depends(_get_svc),
) -> ChantContenuRead:
    contenu = svc.get_contenu(chant_id)
    return ChantContenuRead.model_validate(contenu)


@router.put(
    "/{chant_id}/contenu",
    response_model=ChantContenuRead,
    status_code=status.HTTP_200_OK,
    summary="Créer ou remplacer le contenu ChordPro",
    dependencies=[_ADMIN],
)
def upsert_contenu(
    chant_id: str,
    payload: ChantContenuCreate,
    svc: ChantService = Depends(_get_svc),
) -> ChantContenuRead:
    contenu = svc.upsert_contenu(chant_id, payload)
    return ChantContenuRead.model_validate(contenu)


@router.patch(
    "/{chant_id}/contenu",
    response_model=ChantContenuRead,
    status_code=status.HTTP_200_OK,
    summary="Mettre à jour le contenu avec verrou optimiste",
    dependencies=[_ADMIN],
)
def update_contenu(
    chant_id: str,
    payload: ChantContenuUpdate,
    svc: ChantService = Depends(_get_svc),
) -> ChantContenuRead:
    contenu = svc.update_contenu(chant_id, payload)
    return ChantContenuRead.model_validate(contenu)


@router.post(
    "/{chant_id}/contenu/transpose",
    response_model=ChantTransposeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transposer le contenu (sans sauvegarde)",
    dependencies=[_AUTH],
)
def transpose_contenu(
    chant_id: str,
    payload: ChantTransposeRequest,
    svc: ChantService = Depends(_get_svc),
) -> ChantTransposeResponse:
    orig, new_ton, new_paroles = svc.transpose(chant_id, payload.semitones)
    return ChantTransposeResponse(
        tonalite_originale=orig,
        tonalite_transposee=new_ton,
        paroles_chords=new_paroles,
    )
