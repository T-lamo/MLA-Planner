from typing import List

from fastapi import Depends, HTTPException, Query, status

from core.auth.auth_dependencies import get_current_active_user
from models import (
    DataListResponse,
    ProfilCreateFull,
    ProfilReadFull,
    ProfilSelfUpdate,
    ProfilUpdateFull,
    Utilisateur,
)
from models.base_pagination import PaginatedResponse
from models.campus_model import CampusRead
from models.ministere_model import MinistereSimple
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

# Nettoyage des routes GET / et GET /all, remplacées par des variantes campus.
# Le filtre cible UNIQUEMENT les GET pour ne pas supprimer POST / (create).
router.routes = [
    route
    for route in router.routes
    if not (
        getattr(route, "path", None) in (f"{router.prefix}/", f"{router.prefix}/all")
        and "GET" in getattr(route, "methods", set())
    )
]


# 1b. Route "Mon Profil" — accessible à tout utilisateur authentifié
@router.get(
    "/me",
    response_model=ProfilReadFull,
    summary="Récupère le profil complet de l'utilisateur connecté",
)
def get_my_profile(
    current_user: Utilisateur = Depends(get_current_active_user),
    service: ProfileService = Depends(router_factory.get_service),
):
    """Retourne le ProfilReadFull du membre lié à l'utilisateur connecté."""
    if not current_user.membre_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil membre associé à cet utilisateur.",
        )
    return service.get_one(current_user.membre_id)


# 1c. Mise à jour des infos personnelles — accessible à tout utilisateur authentifié
@router.patch(
    "/me",
    response_model=ProfilReadFull,
    summary="Met à jour les informations personnelles de l'utilisateur connecté",
)
def update_my_profile(
    data: ProfilSelfUpdate,
    current_user: Utilisateur = Depends(get_current_active_user),
    service: ProfileService = Depends(router_factory.get_service),
):
    """Permet à l'utilisateur de modifier nom, prénom, email, téléphone uniquement."""
    if not current_user.membre_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil membre associé à cet utilisateur.",
        )
    payload = ProfilUpdateFull(**data.model_dump(exclude_unset=True))
    return service.update(current_user.membre_id, payload)


# 1d. Campus du membre connecté
@router.get(
    "/me/campuses",
    response_model=List[CampusRead],
    summary="Récupère les campus du membre connecté",
)
def get_my_campuses(
    current_user: Utilisateur = Depends(get_current_active_user),
    service: ProfileService = Depends(router_factory.get_service),
) -> List[CampusRead]:
    """Retourne la liste des campus auxquels appartient le membre connecté."""
    if not current_user.membre_id:
        return []
    profil = service.get_one(current_user.membre_id)
    return list(profil.campuses)


# 1e. Ministères du membre connecté filtrés par campus
@router.get(
    "/me/ministeres/by-campus/{campus_id}",
    response_model=List[MinistereSimple],
    summary="Ministères de l'utilisateur pour un campus donné",
)
def get_my_ministeres_by_campus(
    campus_id: str,
    current_user: Utilisateur = Depends(get_current_active_user),
    service: ProfileService = Depends(router_factory.get_service),
) -> List[MinistereSimple]:
    """Intersection : ministères du profil ∩ ministères liés au campus."""
    if not current_user.membre_id:
        return []
    return service.get_my_ministeres_by_campus(current_user.membre_id, campus_id)


# 2. Surcharge de la route Paginated pour inclure le filtre campus_id
@router.get(
    "/campus/{campus_id}/",
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
    "/campus/{campus_id}/all",
    response_model=DataListResponse[ProfilReadFull],
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
)
def list_all(
    campus_id: str | None = None,
    service: ProfileService = Depends(router_factory.get_service),
):
    """Récupère tous les profils avec filtrage optionnel par campus."""
    print("campus id", campus_id)
    profiles = service.list_all(campus_id=campus_id)
    return {"data": profiles}


# Ensure literal routes (e.g. /me) are evaluated before
# parameterized routes (e.g. /{id})
router.routes.sort(key=lambda r: (1 if "{" in getattr(r, "path", "") else 0))
