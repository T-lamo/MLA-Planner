from models import OrganisationCreate, OrganisationRead
from models.organisation_model import OrganisationUpdate
from routes.deps import SUPER_ADMIN_ONLY_DEPS
from services.organisation_service import OrganisationService

from .base_route_factory import CRUDRouterFactory

# 3. Génération du router via la Factory
org_factory = CRUDRouterFactory(
    service_class=OrganisationService,
    create_schema=OrganisationCreate,
    read_schema=OrganisationRead,
    update_schema=OrganisationUpdate,
    path="/organisations",
    tag="Organisations",
    dependencies=SUPER_ADMIN_ONLY_DEPS,
)

# 4. Export du router propre pour main.py
router = org_factory.router
