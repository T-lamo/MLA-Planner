import logging
from uuid import uuid4

from sqlmodel import Session

from models import (
    PlanningService,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    Slot,
    SlotCreate,
)
from repositories.planning_repository import PlanningRepository  # Lazy import
from services.base_service import BaseService
from services.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class PlanningServiceSvc(
    BaseService[
        PlanningServiceCreate,
        PlanningServiceRead,
        PlanningServiceUpdate,
        PlanningService,
    ]
):
    def __init__(self, db: Session):
        super().__init__(PlanningRepository(db), "Planning")
        self.db = db
        self.validator = ValidationEngine()

    def create(self, data: PlanningServiceCreate) -> PlanningService:
        # 1. Manual validation of Activity existence
        # activite = self.db.get(Activite, data.activite_id)
        # if not activite:
        #     raise BadRequestException(f"Activité {data.activite_id} introuvable.")
        #
        # 2. The BaseService.create will handle the rest
        return super().create(data)

    def create_slot(self, slot_data: SlotCreate) -> Slot:
        # 1. Validation
        self.validator.validate_slot_timing(self.db, slot_data, self.repo)

        # 2. Persistance atomique
        try:
            with self.db.begin_nested():
                new_slot = Slot(id=str(uuid4()), **slot_data.model_dump())
                self.repo.save_slot(new_slot)

            self.db.flush()
            self.db.refresh(new_slot)
            logger.info(f"Slot '{new_slot.nom_creneau}' créé avec succès.")
            return new_slot
        except Exception as e:
            logger.error(f"Erreur lors de la création du slot : {str(e)}")
            raise e
