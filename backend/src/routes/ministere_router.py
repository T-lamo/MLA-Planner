from fastapi import Depends

from models import DataResponse
from models.ministere_model import (
    MinistereCreate,
    MinistereRead,
    MinistereReadWithRelations,
    MinistereUpdate,
)
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.ministere_service import MinistereService

from .base_route_factory import CRUDRouterFactory

ministere_factory = CRUDRouterFactory(
    service_class=MinistereService,
    create_schema=MinistereCreate,
    read_schema=MinistereRead,
    update_schema=MinistereUpdate,
    path="/ministeres",
    tag="Ministères",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = ministere_factory.router


# 2. Surcharge de la route GET /{item_id} pour utiliser le schéma riche
# On définit cette route manuellement pour utiliser 'get_detailed' au lieu de 'get_one'
@router.get(
    "/{item_id}/full",
    response_model=DataResponse[
        MinistereReadWithRelations
    ],  # Utilisation du schéma avec relations
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def get_ministere_detailed(
    item_id: str, service: MinistereService = Depends(ministere_factory.get_service)
):
    """Récupère un ministère avec ses membres, pôles et statistiques."""
    response = service.get_detailed(item_id)
    return {"data": response}
