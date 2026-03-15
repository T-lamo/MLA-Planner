"""
Router de configuration du campus.

Toutes les routes sont protégées par RoleChecker(["Super Admin"]).
Préfixe : /config
"""

from typing import Any, List

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker
from models.campus_config_model import (
    CampusConfigSummary,
    CampusSetupPayload,
    CampusSetupResult,
    CategorieConfigCreate,
    CategorieConfigResponse,
    CategorieConfigUpdate,
    MinistereConfigCreate,
    MinistereConfigResponse,
    MinistereConfigUpdate,
    RbacRolesInitResponse,
    RoleCompetenceConfigCreate,
    RoleCompetenceConfigResponse,
    RoleCompetenceConfigUpdate,
    StatutsInitResponse,
)
from models.campus_model import CampusRead
from models.categorie_role_model import CategorieRoleRead
from models.ministere_model import MinistereRead
from models.role_competence_model import RoleCompetenceRead
from models.role_model import RoleRead
from services.campus_config_service import CampusConfigService

router = APIRouter(
    prefix="/config",
    tags=["Configuration"],
    dependencies=[Depends(RoleChecker(["Super Admin"]))],
)

_DB = Depends(Database.get_db_for_route)


def _get_svc(db: Session = _DB) -> CampusConfigService:  # type: ignore
    return CampusConfigService(db)


# ------------------------------------------------------------------ #
#  STATUTS
# ------------------------------------------------------------------ #


@router.post(
    "/statuts/init",
    response_model=StatutsInitResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialiser les statuts planning et affectation",
)
def init_statuts(
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    """Crée les statuts manquants de façon idempotente."""
    plannings, affectations = svc.init_statuts()
    return StatutsInitResponse(
        statuts_planning=[sp.code for sp in plannings],
        statuts_affectation=[sa.code for sa in affectations],
    )


# ------------------------------------------------------------------ #
#  CAMPUS
# ------------------------------------------------------------------ #


@router.get(
    "/campus",
    response_model=List[CampusRead],
    status_code=status.HTTP_200_OK,
    summary="Lister tous les campus",
)
def list_campus(
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.list_campus()


@router.get(
    "/campus/{campus_id}/summary",
    response_model=CampusConfigSummary,
    status_code=status.HTTP_200_OK,
    summary="Résumé de la configuration d'un campus",
)
def get_campus_summary(
    campus_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.get_campus_summary(campus_id)


@router.post(
    "/campus/{campus_id}/setup",
    response_model=CampusSetupResult,
    status_code=status.HTTP_200_OK,
    summary="Configuration complète d'un campus en une seule requête",
)
def setup_campus(
    campus_id: str,
    body: CampusSetupPayload,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    """
    Configure un campus entièrement (idempotent) :
    ministères, catégories, rôles compétence, RBAC, statuts.
    Retourne le résumé complet après configuration.
    """
    return svc.setup_campus(campus_id, body)


# ------------------------------------------------------------------ #
#  MINISTÈRES
# ------------------------------------------------------------------ #


@router.post(
    "/campus/{campus_id}/ministeres",
    response_model=MinistereConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Ajouter un ministère à un campus (find-or-create)",
)
def add_ministere_to_campus(
    campus_id: str,
    body: MinistereConfigCreate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    ministere, created, linked = svc.add_ministere_to_campus(
        campus_id,
        body.nom,
        description=body.description,
    )
    return MinistereConfigResponse(
        ministere=MinistereRead.model_validate(ministere),
        created=created,
        linked=linked,
    )


@router.delete(
    "/campus/{campus_id}/ministeres/{ministere_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer un ministère d'un campus",
)
def remove_ministere_from_campus(
    campus_id: str,
    ministere_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> None:
    svc.remove_ministere_from_campus(campus_id, ministere_id)


@router.get(
    "/campus/{campus_id}/ministeres",
    response_model=List[MinistereRead],
    status_code=status.HTTP_200_OK,
    summary="Lister les ministères d'un campus",
)
def list_ministeres_of_campus(
    campus_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.list_ministeres_of_campus(campus_id)


# ------------------------------------------------------------------ #
#  CATÉGORIES DE RÔLES
# ------------------------------------------------------------------ #


@router.post(
    "/ministeres/{ministere_id}/categories",
    response_model=CategorieConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Ajouter une catégorie à un ministère (find-or-create)",
)
def add_categorie_to_ministere(
    ministere_id: str,
    body: CategorieConfigCreate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    categorie, created = svc.add_categorie_to_ministere(
        ministere_id,
        body.nom,
        description=body.description,
    )
    return CategorieConfigResponse(
        categorie=CategorieRoleRead.model_validate(categorie),
        created=created,
    )


@router.delete(
    "/ministeres/{ministere_id}/categories/{categorie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une catégorie d'un ministère",
)
def delete_categorie(
    ministere_id: str,
    categorie_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> None:
    svc.delete_categorie(ministere_id, categorie_id)


@router.get(
    "/ministeres/{ministere_id}/categories",
    response_model=List[CategorieRoleRead],
    status_code=status.HTTP_200_OK,
    summary="Lister les catégories d'un ministère",
)
def list_categories_of_ministere(
    ministere_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.list_categories_of_ministere(ministere_id)


# ------------------------------------------------------------------ #
#  RÔLES COMPÉTENCE
# ------------------------------------------------------------------ #


@router.post(
    "/categories/{categorie_id}/roles-competence",
    response_model=RoleCompetenceConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Ajouter un rôle compétence à une catégorie (find-or-create)",
)
def add_role_competence_to_categorie(
    categorie_id: str,
    body: RoleCompetenceConfigCreate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    role_comp, created = svc.add_role_competence_to_categorie(
        categorie_id,
        body.code,
        body.libelle,
        description=body.description,
    )
    return RoleCompetenceConfigResponse(
        role_competence=RoleCompetenceRead.model_validate(role_comp),
        created=created,
    )


@router.delete(
    "/categories/{categorie_id}/roles-competence/{role_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un rôle compétence d'une catégorie",
)
def delete_role_competence(
    categorie_id: str,
    role_code: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> None:
    svc.delete_role_competence(categorie_id, role_code)


@router.post(
    "/categories/{categorie_id}/roles-competence/{role_code}/link",
    response_model=RoleCompetenceConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Rattacher un rôle compétence existant à une catégorie",
)
def link_role_competence_to_categorie(
    categorie_id: str,
    role_code: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    """Réattache un rôle compétence existant (autre catégorie) à cette catégorie."""
    role_comp = svc.link_role_competence_to_categorie(categorie_id, role_code)
    return RoleCompetenceConfigResponse(
        role_competence=RoleCompetenceRead.model_validate(role_comp),
        created=False,
    )


@router.patch(
    "/ministeres/{ministere_id}",
    response_model=MinistereRead,
    status_code=status.HTTP_200_OK,
    summary="Modifier un ministère",
)
def update_ministere(
    ministere_id: str,
    body: MinistereConfigUpdate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.update_ministere(
        ministere_id, nom=body.nom, description=body.description
    )


@router.patch(
    "/ministeres/{ministere_id}/categories/{categorie_id}",
    response_model=CategorieRoleRead,
    status_code=status.HTTP_200_OK,
    summary="Modifier une catégorie",
)
def update_categorie(
    ministere_id: str,
    categorie_id: str,
    body: CategorieConfigUpdate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.update_categorie(
        ministere_id, categorie_id, nom=body.nom, description=body.description
    )


@router.patch(
    "/categories/{categorie_id}/roles-competence/{role_code}",
    response_model=RoleCompetenceRead,
    status_code=status.HTTP_200_OK,
    summary="Modifier un rôle compétence",
)
def update_role_competence_endpoint(
    categorie_id: str,
    role_code: str,
    body: RoleCompetenceConfigUpdate,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    return svc.update_role_competence(
        categorie_id,
        role_code,
        libelle=body.libelle,
        description=body.description,
    )


# ------------------------------------------------------------------ #
#  RBAC
# ------------------------------------------------------------------ #


@router.post(
    "/campus/{campus_id}/ministeres/{ministere_id}/rbac-roles/init",
    response_model=RbacRolesInitResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialiser les rôles RBAC pour un couple campus/ministère",
)
def init_rbac_roles_for_ministere(
    campus_id: str,
    ministere_id: str,
    svc: CampusConfigService = Depends(_get_svc),
) -> Any:
    roles, created_count = svc.init_rbac_roles_for_ministere(campus_id, ministere_id)
    return RbacRolesInitResponse(
        roles=[RoleRead.model_validate(r) for r in roles],
        created_count=created_count,
    )
