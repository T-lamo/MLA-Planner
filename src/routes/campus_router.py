from models.campus_model import CampusCreate, CampusRead, CampusUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.campus_service import CampusService

from .base_route_factory import CRUDRouterFactory

# Génération automatique du router via la Factory
campus_factory = CRUDRouterFactory(
    service_class=CampusService,
    create_schema=CampusCreate,
    read_schema=CampusRead,
    update_schema=CampusUpdate,
    path="/campus",
    tag="Campus",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

# Export du router pour inclusion dans main.py
router = campus_factory.router
