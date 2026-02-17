import logging
from datetime import datetime
from typing import Any, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from core.workflow_engine import WorkflowEngine, planning_transitions
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    Affectation,
    PlanningService,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    Slot,
    SlotCreate,
)
from models.membre_model import MemberAgendaResponse
from models.planning_model import (
    PlanningFullCreate,
    PlanningFullRead,
    PlanningFullUpdate,
    ViewContext,
)
from models.schema_db_model import Activite
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

    # Dans la classe PlanningServiceSvc :

    def get_full_planning(self, planning_id: str) -> PlanningFullRead:
        try:
            # 1. Fetch optimisé (La requête reste ici car elle définit le périmètre du DTO)
            query = (
                select(PlanningService)
                .where(PlanningService.id == planning_id)
                .where(
                    PlanningService.deleted_at == None
                )  # noqa: E711 # pylint: disable=C0121
                .options(
                    selectinload(cast(Any, PlanningService.activite)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.membre)),
                )
            )
            planning_db = self.db.exec(query).first()

            if not planning_db:
                raise AppException(ErrorRegistry.PLAN_NOT_FOUND)

            # 2. Délégation aux services spécialisés
            total, filled = self.slot_svc.get_slots_metrics(planning_db.slots)

            # 3. Calcul du Workflow (propre au Planning)
            current_status = PlanningStatusCode(planning_db.statut_code)
            allowed = self.workflow.get_allowed_transitions(current_status)

            context = ViewContext(
                allowed_transitions=[s.value for s in allowed],
                total_slots=total,
                filled_slots=filled,
                is_ready_for_publish=(total > 0 and filled == total),
            )

            # 4. Assemblage final
            result_dto = PlanningFullRead.model_validate(planning_db)
            result_dto.view_context = context
            return result_dto

        except Exception as e:
            logger.error(f"Erreur get_full_planning ID {planning_id}: {str(e)}")
            raise

    def get_member_agenda_full(
        self, membre_id: str, campus_id: str, start: datetime, end: datetime
    ):
        # 1. Requête SQL avec jointures (optimisation des performances)
        query = (
            select(Affectation)
            .join(Slot)
            .join(PlanningService)
            .join(Activite)
            .where(Affectation.membre_id == membre_id)
            .where(Activite.campus_id == campus_id)
            .where(Slot.date_debut >= start)
            .where(Slot.date_debut <= end)
            .options(
                selectinload(cast(Any, Affectation.slot))
                .selectinload(cast(Any, Slot.planning))
                .selectinload(cast(Any, PlanningService.activite))
                .selectinload(cast(Any, Activite.campus))
            )
        )
        results = self.db.exec(query).all()
        affectations = list(results)

        # 2. Appel au SlotService (qui lui-même appellera AffectationService)
        entries = self.slot_svc.map_affectations_to_entries(affectations)
        stats = self.slot_svc.get_agenda_statistics(affectations)

        # 3. Rassemblement final
        return MemberAgendaResponse(
            period_start=start, period_end=end, statistics=stats, entries=entries
        )
