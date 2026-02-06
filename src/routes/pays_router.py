from models import PaysCreate, PaysRead
from models.pays_model import PaysUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.pays_service import PaysService

from .base_route_factory import CRUDRouterFactory

# 3. Génération automatique du router via la Factory
pays_factory = CRUDRouterFactory(
    service_class=PaysService,
    create_schema=PaysCreate,
    read_schema=PaysRead,
    update_schema=PaysUpdate,
    path="/pays",
    tag="Pays",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

# 4. Export du router pour main.py
router = pays_factory.router
