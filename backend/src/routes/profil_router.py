from typing import List, Optional

from fastapi import Depends, Query

from models import ProfilCreateFull, ProfilReadFull, ProfilUpdateFull
from models.base_pagination import PaginatedResponse
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.profile_service import ProfileService

from .base_route_factory import CRUDRouterFactory

# Initialisation via la Factory
router_factory = CRUDRouterFactory(
    service_class=ProfileService,
    create_schema=ProfilCreateFull,
    read_schema=ProfilReadFull,
    update_schema=ProfilUpdateFull,
    path="/profiles",  # Changé de /poles à /profiles
    tag="Profiles",  # Changé de Poles à Profiles
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)
router = router_factory.router

# Nettoyage des routes existantes avec check de type pour mypy
router.routes = [
    route
    for route in router.routes
    if getattr(route, "path", None) not in (f"{router.prefix}/", f"{router.prefix}/all")
]


# 2. Surcharge de la route Paginated pour inclure le filtre campus_id
@router.get(
    "/",
    response_model=PaginatedResponse[ProfilReadFull],
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def list_paginated(
    campus_id: str | None = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ProfileService = Depends(router_factory.get_service),
):
    """Récupère la liste des profils avec filtrage optionnel par campus."""

    # On s'assure que c'est une string pure
    return service.list_paginated(limit=limit, offset=offset, campus_id=campus_id)


# 3. Surcharge de la route All pour inclure le filtre campus_id
@router.get(
    "/all",
    response_model=List[ProfilReadFull],
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def list_all_profiles(
    campus_id: Optional[str] = Query(None, description="Filtrer par l'ID du campus"),
    service: ProfileService = Depends(router_factory.get_service),
):
    """Récupère tous les profils avec filtrage optionnel par campus."""
    return service.list_all(campus_id=campus_id)
