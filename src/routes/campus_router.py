from fastapi import Depends

from core.auth.auth_dependencies import RoleChecker
from models.campus_model import CampusCreate, CampusRead, CampusUpdate
from services.campus_service import CampusService

from .base_route_factory import CRUDRouterFactory

# Définition des dépendances de rôles
admin_only = Depends(RoleChecker(["ADMIN"]))

# Configuration des accès : Create/Update/Delete réservés aux Admins
campus_deps = {
    "create": [admin_only],
    "update": [admin_only],
    "delete": [admin_only],
    "read": [],  # Lecture publique (ou ajoutez une dépendance si besoin)
}

# Génération automatique du router via la Factory
campus_factory = CRUDRouterFactory(
    service_class=CampusService,
    create_schema=CampusCreate,
    read_schema=CampusRead,
    update_schema=CampusUpdate,
    path="/campus",
    tag="Campus",
    dependencies=campus_deps,
)

# Export du router pour inclusion dans main.py
router = campus_factory.router
