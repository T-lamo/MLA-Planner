from models import OrganisationICCCreate, OrganisationICCRead
from models.organisationicc_model import OrganisationICCUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.organisation_service import OrganisationService

from .base_route_factory import CRUDRouterFactory

# 3. Génération du router via la Factory
org_factory = CRUDRouterFactory(
    service_class=OrganisationService,
    create_schema=OrganisationICCCreate,
    read_schema=OrganisationICCRead,
    update_schema=OrganisationICCUpdate,
    path="/organisations",
    tag="Organisations",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

# 4. Export du router propre pour main.py
router = org_factory.router
