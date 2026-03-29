from typing import Optional

from fastapi import Depends, Query

from models import (
    RoleCompetenceCreate,
    RoleCompetenceRead,
    RoleCompetenceUpdate,
    RolesByCategoryResponse,
)
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.role_competence_service import RoleCompetenceService

from .base_route_factory import CRUDRouterFactory

factory = CRUDRouterFactory(
    service_class=RoleCompetenceService,
    create_schema=RoleCompetenceCreate,
    read_schema=RoleCompetenceRead,
    update_schema=RoleCompetenceUpdate,
    path="/roles-competences",
    tag="Rôles & Compétences",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router


@router.get(
    "/by-category/full",
    response_model=RolesByCategoryResponse,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def get_roles_grouped(
    ministere_id: Optional[str] = Query(
        None, description="Filtrer par ministère (rôles actifs uniquement)"
    ),
    service: RoleCompetenceService = Depends(factory.get_service),
):
    """Retourne les rôles groupés par catégorie pour l'affichage UI.

    Si ministere_id est fourni, seuls les rôles activés pour ce ministère
    (via t_ministere_role_config) sont retournés.
    """
    return {"data": service.list_grouped_by_category(ministere_id=ministere_id)}
