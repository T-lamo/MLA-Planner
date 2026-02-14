from models import ActiviteCreate, ActiviteRead, ActiviteUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS  # Chemin selon votre projet
from services.activite_service import ActiviteService

from .base_route_factory import CRUDRouterFactory

# On utilise la factory pour générer les routes standards
factory = CRUDRouterFactory(
    service_class=ActiviteService,
    create_schema=ActiviteCreate,
    read_schema=ActiviteRead,
    update_schema=ActiviteUpdate,
    path="/activities",
    tag="Activités",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router
