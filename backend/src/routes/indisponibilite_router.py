from models import IndisponibiliteCreate, IndisponibiliteRead, IndisponibiliteUpdate
from routes.base_route_factory import CRUDRouterFactory
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.indisponibilite_service import IndisponibiliteService

factory = CRUDRouterFactory(
    service_class=IndisponibiliteService,
    create_schema=IndisponibiliteCreate,
    read_schema=IndisponibiliteRead,
    update_schema=IndisponibiliteUpdate,
    path="/indisponibilites",
    tag="Indisponibilités",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router
