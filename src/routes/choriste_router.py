# src/routes/choriste_route.py

from models.choriste_model import ChoristeCreate, ChoristeRead, ChoristeUpdate
from routes.base_route_factory import CRUDRouterFactory
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.choriste_service import ChoristeService

factory = CRUDRouterFactory(
    service_class=ChoristeService,
    create_schema=ChoristeCreate,
    read_schema=ChoristeRead,
    update_schema=ChoristeUpdate,
    path="/choristes",
    tag="Choristes",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router
