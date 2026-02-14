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
from models.planning_model import PlanningFullCreate
from repositories.planning_repository import PlanningRepository  # Lazy import
from services.activite_service import ActiviteService
from services.assignement_service import AssignmentService
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

    def create_full_planning(self, data: PlanningFullCreate) -> PlanningService:
        logger.info("Début de l'orchestration du planning complet")
        try:
            with self.db.begin_nested():
                # 1. Activité
                activite_svc = ActiviteService(self.db)
                activite_db = activite_svc.create(data.activite)

                # 2. Planning
                statut_code = (
                    data.planning.statut_code if data.planning else "BROUILLON"
                )
                p_data = PlanningServiceCreate(
                    activite_id=activite_db.id, statut_code=statut_code
                )
                planning_db = self.create(p_data)

                # 3. Slots
                assignment_svc = AssignmentService(self.db)
                for s_nested in data.slots:
                    # On convertit le SlotFullNested en SlotCreate pour le validator
                    s_create = SlotCreate(
                        nom_creneau=s_nested.nom_creneau,
                        date_debut=s_nested.date_debut,
                        date_fin=s_nested.date_fin,
                        planning_id=planning_db.id,  # Injecté ici
                    )
                    slot_db = self.create_slot(s_create)

                    # 4. Affectations
                    for a_data in s_nested.affectations:
                        assignment_svc.assign_member_to_slot(
                            slot_id=slot_db.id,
                            membre_id=a_data.membre_id,
                            role_code=a_data.role_code,
                        )
            self.db.commit()
            return planning_db
        except Exception as e:
            raise e
