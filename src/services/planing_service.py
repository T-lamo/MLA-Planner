import logging

from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
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
from utils.utils_func import extract_field

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

        # Injection des services dépendants pour éviter les réinstanciations
        self.activite_svc = ActiviteService(self.db)
        self.slot_svc = SlotService(self.db)

    def _on_publish_hook(self, planning: PlanningService):
        logger.info(f"Déclenchement des notifications pour le planning {planning.id}")
        # Logique d'envoi de mail/push ici

    def update_planning_status(
        self, planning_id: str, new_status: PlanningStatusCode, auto_flush: bool = True
    ) -> PlanningService:
        """Met à jour le statut avec gestion du workflow."""
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

        if auto_flush:
            self.db.flush()

        return planning

    def create_slot(self, slot_data: SlotCreate) -> Slot:
        """Délégué au SlotService."""
        return self.slot_svc.add_slot_to_planning(slot_data.planning_id, slot_data)

    def create_full_planning(self, data: PlanningFullCreate) -> PlanningService:
        """Crée un planning complet (Activité + Planning
        + Slots + Affectations) de façon atomique."""
        logger.info("Début création planning complet")
        try:
            # 1. Création de l'Activité
            activite_db = self.activite_svc.create(data.activite)

            # 2. Création du Planning
            statut_initial = extract_field(
                data.planning, "statut_code", PlanningStatusCode.BROUILLON.value
            )

            p_create = PlanningServiceCreate(
                activite_id=activite_db.id, statut_code=statut_initial
            )
            planning_db = self.create(p_create)

            # 3. Synchronisation des Slots & Affectations
            self.slot_svc.sync_planning_slots(planning_db.id, data.slots)

            self.db.flush()
            self.db.refresh(planning_db)
            return planning_db

        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_CREATION_ERROR.message.format(error=str(e))
            )
            raise e

    def update_full_planning(
        self, planning_id: str, data: PlanningFullUpdate
    ) -> PlanningService:
        planning = self.get_one(planning_id)

        if planning.statut_code in [
            PlanningStatusCode.TERMINE.value,
            PlanningStatusCode.ANNULE.value,
        ]:
            raise AppException(
                ErrorRegistry.PLANNING_IMMUTABLE, status=planning.statut_code
            )

        try:
            # 1. Mise à jour du Statut
            new_status_code = extract_field(data.planning, "statut_code")
            if new_status_code and new_status_code != planning.statut_code:
                self.update_planning_status(
                    planning_id, PlanningStatusCode(new_status_code), auto_flush=False
                )

            # 2. Mise à jour de l'Activité
            if data.activite:
                if not planning.activite_id:
                    raise AppException(ErrorRegistry.PLANNING_ACTIVITY_MISSING)

                self.activite_svc.update(str(planning.activite_id), data.activite)

            # 3. Synchronisation Slots
            slots_payload = extract_field(data, "slots", [])
            self.slot_svc.sync_planning_slots(planning.id, slots_payload)

            self.db.flush()
            self.db.refresh(planning)
            return planning

        except AppException:
            # On laisse remonter nos exceptions métier typées
            raise
        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_UPDATE_ERROR.message.format(
                    id=planning_id, error=str(e)
                )
            )
            raise e

    def delete_full_planning(self, planning_id: str) -> None:
        planning = self.get_one(planning_id)
        activite_id = planning.activite_id

        if planning.statut_code in [
            PlanningStatusCode.PUBLIE.value,
            PlanningStatusCode.TERMINE.value,
        ]:
            raise AppException(
                ErrorRegistry.PLANNING_DELETE_IMPOSSIBLE, status=planning.statut_code
            )

        try:
            self.slot_svc.delete_by_planning(planning_id)
            self.db.delete(planning)
            self.db.flush()

            if not activite_id:
                logger.warning(
                    ErrorRegistry.PLANNING_DELETED_WITHOUT_ACTIVITY.message.format(
                        id=planning_id
                    )
                )
            else:
                self.activite_svc.hard_delete(str(activite_id))

            logger.info(f"Full Delete réussi : Planning {planning_id}")
        except AppException:
            raise
        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_DELETE_ERROR.message.format(
                    id=planning_id, error=str(e)
                )
            )
            raise e
