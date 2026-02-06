from models.pole_model import PoleCreate, PoleRead, PoleUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.pole_service import PoleService

from .base_route_factory import CRUDRouterFactory

router_factory = CRUDRouterFactory(
    service_class=PoleService,
    create_schema=PoleCreate,
    read_schema=PoleRead,
    update_schema=PoleUpdate,
    path="/poles",
    tag="Poles",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = router_factory.router
