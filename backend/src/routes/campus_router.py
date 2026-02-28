from typing import Any, List, cast

from fastapi import Body, Depends, status

from models.campus_model import (
    CampusCreate,
    CampusRead,
    CampusReadWithDetails,
    CampusUpdate,
)
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.campus_service import CampusService

from .base_route_factory import CRUDRouterFactory

# 1. Initialisation de la Factory
campus_factory = CRUDRouterFactory(
    service_class=CampusService,
    create_schema=CampusCreate,
    read_schema=CampusRead,
    update_schema=CampusUpdate,
    path="/campus",
    tag="Campus",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = campus_factory.router


# 2. Ajout de routes spécifiques en réutilisant la dépendance de la factory
@router.post(
    "/{campus_id}/ministeres",
    response_model=CampusReadWithDetails,
    status_code=status.HTTP_200_OK,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("update", []),
    summary="Lier des ministères à un campus",
)
def link_ministeres_to_campus(
    campus_id: str,
    ministere_ids: List[str] = Body(..., description="Liste des UUIDs des ministères"),
    # On récupère get_service directement de la factory
    service: CampusService = Depends(campus_factory.get_service),
) -> Any:
    """
    Endpoint pour synchroniser les ministères d'un campus (Many-to-Many).
    """
    # Cast utile pour Mypy si la factory utilise du générique Any
    svc = cast(CampusService, service)
    return svc.link_ministeres(campus_id, ministere_ids)


@router.patch(
    "/{campus_id}/ministeres/{ministere_id}",
    response_model=CampusReadWithDetails,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("update", []),
    summary="Ajouter un ministère spécifique",
)
def add_single_ministere_to_campus(
    campus_id: str,
    ministere_id: str,
    service: CampusService = Depends(campus_factory.get_service),
) -> Any:
    """
    Ajoute un ministère à la collection existante sans écraser les autres.
    """
    svc = cast(CampusService, service)
    return svc.add_single_ministere(campus_id, ministere_id)


@router.get(
    "/{campus_id}/details",
    response_model=CampusReadWithDetails,
    dependencies=STANDARD_ADMIN_ONLY_DEPS.get("read", []),
    summary="Récupérer un campus avec ses ministères et membres",
)
def get_campus_full_details(
    campus_id: str,
    service: CampusService = Depends(campus_factory.get_service),
) -> Any:
    """
    Retourne une vue agrégée du campus incluant les relations
    Many-to-Many et One-to-Many.
    """
    svc = cast(CampusService, service)
    return svc.get_details(campus_id)
