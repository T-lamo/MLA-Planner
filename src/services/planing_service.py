# src/services/planning_service.py
import logging

from sqlmodel import Session

from core.exceptions.exceptions import BadRequestException
from core.workflow_engine import WorkflowEngine, planning_transitions
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    PlanningService,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    Slot,
    SlotCreate,
)
from models.planning_model import PlanningFullCreate, PlanningFullUpdate
from repositories.planning_repository import PlanningRepository
from services.activite_service import ActiviteService
from services.slot_service import SlotService

from .base_service import BaseService

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
        self.workflow = WorkflowEngine[PlanningStatusCode](planning_transitions)

    def _on_publish_hook(self, planning: PlanningService):
        logger.info(f"Déclenchement des notifications pour le planning {planning.id}")
        # Logique d'envoi de mail/push ici

    def update_planning_status(
        self, planning_id: str, new_status: PlanningStatusCode
    ) -> PlanningService:
        planning = self.get_one(planning_id)
        current_status = PlanningStatusCode(planning.statut_code)

        self.workflow.execute_transition(
            current_status,
            new_status,
            hook=lambda: (
                self._on_publish_hook(planning)
                if new_status == PlanningStatusCode.PUBLIE
                else None
            ),
        )

        planning.statut_code = new_status.value
        self.db.add(planning)
        self.db.flush()
        return planning

    def create_slot(self, slot_data: SlotCreate) -> Slot:
        """
        Rétablit la méthode pour corriger l'erreur src/routes/planning_router.py:53.
        Délégué au SlotService.
        """
        return SlotService(self.db).add_slot_to_planning(
            slot_data.planning_id, slot_data
        )

    def create_full_planning(self, data: PlanningFullCreate) -> PlanningService:
        """Crée un planning complet de façon atomique."""
        logger.info("Début création planning complet")
        try:
            # 1. Activité
            activite_svc = ActiviteService(self.db)
            activite_db = activite_svc.create(data.activite)

            # 2. Planning
            statut_initial = (
                data.planning.statut_code
                if data.planning
                else PlanningStatusCode.BROUILLON.value
            )
            p_create = PlanningServiceCreate(
                activite_id=activite_db.id, statut_code=statut_initial
            )
            planning_db = self.create(p_create)

            # 3. Slots & Affectations
            SlotService(self.db).sync_planning_slots(planning_db.id, data.slots)
            self.db.flush()
            self.db.refresh(planning_db)
            return planning_db
        except Exception as e:
            logger.error(f"Erreur création planning complet : {str(e)}")
            raise e

    def update_full_planning(
        self, planning_id: str, data: PlanningFullUpdate
    ) -> PlanningService:
        """Met à jour l'intégralité du planning de façon atomique."""
        planning = self.get_one(planning_id)

        # 1. Vérification d'immutabilité
        if planning.statut_code in [
            PlanningStatusCode.TERMINE.value,
            PlanningStatusCode.ANNULE.value,
        ]:
            raise BadRequestException(
                f"Planning {planning.statut_code}, modification interdite."
            )

        try:
            # 2. Mise à jour du Statut
            # Après (Nouvelle structure)
            if data.planning and data.planning.statut_code:
                if data.planning.statut_code != planning.statut_code:
                    self.update_planning_status(
                        planning_id, PlanningStatusCode(data.planning.statut_code)
                    )

            # 3. Mise à jour de l'Activité
            if data.activite:
                ActiviteService(self.db).update(planning.activite_id, data.activite)

            # 4. Synchronisation Slots/Affectations
            SlotService(self.db).sync_planning_slots(planning.id, data.slots)

            self.db.flush()
            self.db.refresh(planning)
            return planning
        except Exception as e:
            logger.error(f"Échec update complet : {str(e)}")
            raise e
