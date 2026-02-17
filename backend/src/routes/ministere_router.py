from models.ministere_model import MinistereCreate, MinistereRead, MinistereUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.ministere_service import MinistereService

from .base_route_factory import CRUDRouterFactory

ministere_factory = CRUDRouterFactory(
    service_class=MinistereService,
    create_schema=MinistereCreate,
    read_schema=MinistereRead,
    update_schema=MinistereUpdate,
    path="/ministeres",
    tag="Ministères",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = ministere_factory.router
