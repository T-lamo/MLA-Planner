from fastapi import Depends

from core.auth.auth_dependencies import RoleChecker
from models import OrganisationICCCreate, OrganisationICCRead
from models.organisationicc_model import OrganisationICCUpdate
from services.organisation_service import OrganisationService

from .base_route_factory import CRUDRouterFactory

# 1. Définition des dépendances (admin_only est réutilisé)
admin_only = Depends(RoleChecker(["ADMIN"]))

# 2. Configuration fine des permissions par action
# On peut laisser "read" vide pour un accès public ou ajouter admin_only
org_dependencies = {
    "create": [admin_only],
    "update": [admin_only],
    "delete": [admin_only],
    "read": [],
}

# 3. Génération du router via la Factory
org_factory = CRUDRouterFactory(
    service_class=OrganisationService,
    create_schema=OrganisationICCCreate,
    read_schema=OrganisationICCRead,
    update_schema=OrganisationICCUpdate,
    path="/organisations",
    tag="Organisations",
    dependencies=org_dependencies,
)

# 4. Export du router propre pour main.py
router = org_factory.router
