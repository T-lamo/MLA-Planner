from models import RoleCompetenceCreate, RoleCompetenceRead, RoleCompetenceUpdate
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
