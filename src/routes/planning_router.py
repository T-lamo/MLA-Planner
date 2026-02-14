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
from models.planning_model import PlanningFullCreate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.planing_service import PlanningServiceSvc
from services.slot_service import SlotService

from .base_route_factory import CRUDRouterFactory

# Router pour Planning
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
    "/{planning_id}/slots", response_model=SlotRead, status_code=status.HTTP_201_CREATED
)
def create_slot_for_planning(
    planning_id: str, data: SlotCreate, db: Session = Depends(Database.get_db_for_route)
):
    """Route experte : Ajoute un créneau à un planning
    spécifique avec validation de conflit."""
    svc = PlanningServiceSvc(db)
    # This call to get_one() will raise the NotFoundException (404)
    # defined in your BaseService if the ID doesn't exist.
    svc.get_one(planning_id)

    slot_svc = SlotService(db)
    return slot_svc.add_slot_to_planning(planning_id, data)


@router.post("/slots", response_model=SlotRead, status_code=status.HTTP_201_CREATED)
def add_slot(slot_data: SlotCreate, db: Session = Depends(Database.get_db_for_route)):
    service = PlanningServiceSvc(db)
    return service.create_slot(slot_data)


@router.post(
    "/full", response_model=PlanningServiceRead, status_code=status.HTTP_201_CREATED
)
def create_full_planning_endpoint(
    data: PlanningFullCreate, db: Session = Depends(Database.get_db_for_route)
):
    svc = PlanningServiceSvc(db)
    return svc.create_full_planning(data)


@router.patch("/{planning_id}/status", response_model=PlanningServiceRead)
def change_planning_status(
    planning_id: str,
    new_status: PlanningStatusCode,
    db: Session = Depends(Database.get_db_for_route),
    # factory.get_service injecte Database.get_db_for_route automatiquement
):
    svc = PlanningServiceSvc(db)
    return svc.update_planning_status(planning_id, new_status)
