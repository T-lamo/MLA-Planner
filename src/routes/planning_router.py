from fastapi import Depends, status
from sqlmodel import Session

from conf.db.database import Database
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    SlotCreate,
    SlotRead,
)
from models.planning_model import (
    PlanningFullCreate,
    PlanningFullRead,
    PlanningFullUpdate,
)
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.planing_service import PlanningServiceSvc
from services.slot_service import SlotService

from .base_route_factory import CRUDRouterFactory

# Configuration du Router Factory pour Planning
factory = CRUDRouterFactory(
    service_class=PlanningServiceSvc,
    create_schema=PlanningServiceCreate,
    read_schema=PlanningServiceRead,
    update_schema=PlanningServiceUpdate,
    path="/plannings",
    tag="Plannings",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)
router = factory.router


@router.post(
    "/{planning_id}/slots",
    response_model=SlotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un créneau à un planning existant",
    description=(
        "Crée un nouveau créneau lié à un planning spécifique. "
        "Vérifie la cohérence temporelle avec l'activité parente."
    ),
)
def create_slot_for_planning(
    planning_id: str,
    data: SlotCreate,
    db: Session = Depends(Database.get_db_for_route),
):
    """Point d'entrée pour l'ajout unitaire de créneaux."""
    svc = PlanningServiceSvc(db)
    svc.get_one(planning_id)
    slot_svc = SlotService(db)
    return slot_svc.add_slot_to_planning(planning_id, data)


@router.post(
    "/slots",
    response_model=SlotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Création directe de créneau",
    description="Permet de créer un créneau en spécifiant directement le planning_id.",
)
def add_slot(slot_data: SlotCreate, db: Session = Depends(Database.get_db_for_route)):
    service = PlanningServiceSvc(db)
    return service.create_slot(slot_data)


@router.post(
    "/full",
    response_model=PlanningServiceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Création complète (Activité + Planning + Slots)",
    description=(
        "Point d'entrée atomique pour créer tout l'écosystème d'un planning. "
        "Valide les rôles des membres et l'absence de collisions."
    ),
)
def create_full_planning_endpoint(
    data: PlanningFullCreate,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    return svc.create_full_planning(data)


@router.patch(
    "/{planning_id}/full",
    response_model=PlanningServiceRead,
    status_code=status.HTTP_200_OK,
    summary="Mise à jour intégrale et synchronisation",
    description=(
        "Met à jour l'activité et le planning. Synchronise les slots : "
        "ajoute les nouveaux, met à jour les existants, supprime les absents."
    ),
)
def update_full_planning_endpoint(
    planning_id: str,
    data: PlanningFullUpdate,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    return svc.update_full_planning(planning_id, data)


@router.patch(
    "/{planning_id}/status",
    response_model=PlanningServiceRead,
    summary="Changer le statut du workflow",
    description=(
        "Fait progresser le planning dans son cycle de vie "
        "(ex: de BROUILLON à PUBLIE ou ANNULE)."
    ),
)
def change_planning_status(
    planning_id: str,
    new_status: PlanningStatusCode,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    return svc.update_planning_status(planning_id, new_status)


@router.delete(
    "/{planning_id}/full",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Suppression totale (Cascade descendante)",
    description=(
        "Supprime le planning, ses slots, ses affectations et l'activité associée. "
        "Opération irréversible soumise à validation de statut."
    ),
)
def delete_full_planning_endpoint(
    planning_id: str, db: Session = Depends(Database.get_db_for_route)
):
    """Exécute la suppression complète via le service expert."""
    svc = PlanningServiceSvc(db)
    svc.delete_full_planning(planning_id)


@router.get("/{planning_id}/full", response_model=PlanningFullRead)
def read_full_planning(
    planning_id: str, db: Session = Depends(Database.get_db_for_route)
):
    svc = PlanningServiceSvc(db)
    # On récupère d'abord les infos de base pour vérifier la sécurité
    # planning = svc.get_one(id)

    return svc.get_full_planning(planning_id)
