from fastapi import Depends

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
def get_roles_grouped(service: RoleCompetenceService = Depends(factory.get_service)):
    """Retourne les rôles groupés par catégorie pour l'affichage UI."""
    return {"data": service.list_grouped_by_category()}
