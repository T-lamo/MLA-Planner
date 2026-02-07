from models.chantre_model import ChantreCreate, ChantreRead, ChantreUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.chantre_service import ChantreService

from .base_route_factory import CRUDRouterFactory

factory = CRUDRouterFactory(
    service_class=ChantreService,
    create_schema=ChantreCreate,
    read_schema=ChantreRead,
    update_schema=ChantreUpdate,
    path="/chantres",
    tag="Chantres",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)
router = factory.router
