# src/routes/affectation_router.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import CapabilityChecker, get_current_active_user
from mla_enum.custom_enum import AffectationStatusCode
from models import AffectationCreate, AffectationRead, AffectationUpdate, Utilisateur
from models.affectation_model import AffectationMemberRead
from models.base_pagination import PaginatedResponse
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.affectation_service import AffectationService

from .base_route_factory import CRUDRouterFactory

# Routes spécifiques /me — doivent être déclarées AVANT le factory (qui a /{id})
# pour éviter que FastAPI capture "/me" comme un item_id.
me_router = APIRouter(prefix="/affectations", tags=["Affectations"])


@me_router.get("/me", response_model=PaginatedResponse[AffectationMemberRead])
def get_my_affectations(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Utilisateur = Depends(get_current_active_user),
    db: Session = Depends(Database.get_db_for_route),
) -> PaginatedResponse[AffectationMemberRead]:
    """Retourne les affectations paginées du membre connecté."""
    if not current_user.membre_id:
        return PaginatedResponse(total=0, limit=limit, offset=offset, data=[])
    service = AffectationService(db)
    return service.get_my_affectations(
        current_user.membre_id, limit=limit, offset=offset
    )


@me_router.get("/me/pending-count", response_model=int)
def get_pending_count(
    current_user: Utilisateur = Depends(get_current_active_user),
    db: Session = Depends(Database.get_db_for_route),
) -> int:
    """Nombre d'affectations en attente (PROPOSE) pour le membre connecté."""
    if not current_user.membre_id:
        return 0
    service = AffectationService(db)
    return service.get_pending_count(current_user.membre_id)


# Factory CRUD — génère GET /, GET /all, GET /{id}, POST /, PATCH /{id}, DELETE /{id}
factory = CRUDRouterFactory(
    service_class=AffectationService,
    create_schema=AffectationCreate,
    read_schema=AffectationRead,
    update_schema=AffectationUpdate,
    path="/affectations",
    tag="Affectations",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router

admin_or_resp = Depends(CapabilityChecker(["PLANNING_WRITE"]))


@router.patch("/{affectation_id}/my-status")
def change_my_affectation_status(
    affectation_id: str,
    new_status: AffectationStatusCode,
    current_user: Utilisateur = Depends(get_current_active_user),
    db: Session = Depends(Database.get_db_for_route),
):
    """Accepte ou refuse une affectation (PROPOSE→CONFIRME/REFUSE, membre seul)."""
    membre_id = current_user.membre_id or ""
    service = AffectationService(db)
    return service.update_my_affectation_status(
        affectation_id, new_status, membre_id=membre_id
    )


@router.patch(
    "/{affectation_id}/status",
    dependencies=[admin_or_resp],
)
def change_affectation_status(
    affectation_id: str,
    new_status: AffectationStatusCode,
    db: Session = Depends(Database.get_db_for_route),
):
    """Change le statut d'une affectation (Admin/Responsable)."""
    service = AffectationService(db)
    return service.update_affectation_status(affectation_id, new_status)
