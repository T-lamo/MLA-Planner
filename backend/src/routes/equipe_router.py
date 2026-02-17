from fastapi import Depends, status
from models import EquipeCreate, EquipeRead, EquipeUpdate
from routes.base_route_factory import CRUDRouterFactory
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.equipe_service import EquipeService

# 1. CRUD Standard via Factory
factory = CRUDRouterFactory(
    service_class=EquipeService,
    create_schema=EquipeCreate,
    read_schema=EquipeRead,
    update_schema=EquipeUpdate,
    path="/equipes",
    tag="Equipes",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router


# 2. Endpoints Spécifiques (Actions sur la table de liaison)
@router.post("/{equipe_id}/membres/{membre_id}", status_code=status.HTTP_201_CREATED)
def add_membre_to_equipe(
    equipe_id: str,
    membre_id: str,
    service: EquipeService = Depends(factory.get_service),
):
    return service.add_member(equipe_id, membre_id)


@router.delete(
    "/{equipe_id}/membres/{membre_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_membre_from_equipe(
    equipe_id: str,
    membre_id: str,
    service: EquipeService = Depends(factory.get_service),
):
    service.remove_member(equipe_id, membre_id)
