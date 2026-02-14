# src/routes/planning_routes.py
from fastapi import Depends
from sqlmodel import Session

from conf.db.database import Database
from mla_enum.custom_enum import AffectationStatusCode
from models import AffectationCreate, AffectationRead, AffectationUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.affectation_service import AffectationService
from services.assignement_service import AssignmentService

from .base_route_factory import CRUDRouterFactory

# 2. Routes pour AFFECTATIONS
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


# 3. Extension spécifique pour les validations métiers (Affectation)
# @router.post("/confirm/{aff_id}", tags=["Affectations"])
# def confirm_presence(aff_id: str, db: Session = Depends(Database.get_session)):
#     svc = AffectationService(db)
#     return svc.update(aff_id, {"presence_confirmee": True})


# Router spécifique pour Affectation (logique de création surchargée)


@router.post("/", response_model=AffectationRead)
def create_affectation(
    data: AffectationCreate, db: Session = Depends(Database.get_session)
):
    return AffectationService(db).create_affectation(data)


@router.patch("/{affectation_id}/status")
def change_affectation_status(
    affectation_id: str,
    new_status: AffectationStatusCode,
    db: Session = Depends(Database.get_db_for_route),
):
    """Change le statut d'une affectation (PROPOSE -> CONFIRME, etc.)."""
    service = AssignmentService(db)
    return service.update_affectation_status(affectation_id, new_status)
