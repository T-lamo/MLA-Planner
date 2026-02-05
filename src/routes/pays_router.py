from fastapi import Depends

from core.auth.auth_dependencies import RoleChecker
from models import PaysCreate, PaysRead
from models.pays_model import PaysUpdate
from services.pays_service import PaysService

from .base_route_factory import CRUDRouterFactory

# 1. Définition des dépendances
admin_only = Depends(RoleChecker(["ADMIN"]))

# 2. Configuration des accès par action
pays_dependencies = {
    "create": [admin_only],
    "update": [admin_only],
    "delete": [admin_only],
    "read": [],  # Lecture publique
}

# 3. Génération automatique du router via la Factory
pays_factory = CRUDRouterFactory(
    service_class=PaysService,
    create_schema=PaysCreate,
    read_schema=PaysRead,
    update_schema=PaysUpdate,
    path="/pays",
    tag="Pays",
    dependencies=pays_dependencies,
)

# 4. Export du router pour main.py
router = pays_factory.router
