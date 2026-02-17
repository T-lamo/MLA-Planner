from models import CategorieRoleCreate, CategorieRoleRead, CategorieRoleUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.categorie_role_service import CategorieRoleService

from .base_route_factory import CRUDRouterFactory

factory = CRUDRouterFactory(
    service_class=CategorieRoleService,
    create_schema=CategorieRoleCreate,
    read_schema=CategorieRoleRead,
    update_schema=CategorieRoleUpdate,
    path="/categories-roles",
    tag="Catégories de Rôles",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router
