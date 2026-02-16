import logging
from typing import Any, List, Optional

from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from core.workflow_engine import WorkflowEngine, affectation_transitions
from mla_enum.custom_enum import AffectationStatusCode, PlanningStatusCode
from models import Affectation, PlanningService, Slot
from repositories.planning_repository import PlanningRepository
from services.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PlanningRepository(db)
        self.validator = ValidationEngine()
        self.workflow = WorkflowEngine[AffectationStatusCode](affectation_transitions)

    def _validate_pointing_status(self, planning: Optional[PlanningService]):
        """
        Mutualisation de la règle métier :
        Le pointage (PRESENT/ABSENT) requiert un planning publié.
        """
        if not planning:
            raise AppException(ErrorRegistry.ASSIGNMENT_PLANNING_NOT_FOUND)

        if planning.statut_code != PlanningStatusCode.PUBLIE.value:
            raise AppException(ErrorRegistry.PLANNING_NOT_PUBLISHED)

    def assign_member_to_slot(
        self,
        slot_id: str,
        membre_id: str,
        role_code: str,
        status: Optional[AffectationStatusCode] = None,
    ) -> Affectation:
        self.validator.validate_member_for_slot(self.db, membre_id, slot_id, role_code)

        final_status = status or AffectationStatusCode.PROPOSE

        # Vérification du planning pour les statuts de pointage
        if final_status in [
            AffectationStatusCode.PRESENT,
            AffectationStatusCode.ABSENT,
        ]:
            slot = self.db.get(Slot, slot_id)
            if not slot:
                raise AppException(ErrorRegistry.SLOT_NOT_FOUND, id=slot_id)

            planning = self.db.get(PlanningService, slot.planning_id)
            self._validate_pointing_status(planning)

        new_affectation = Affectation(
            slot_id=slot_id,
            membre_id=membre_id,
            role_code=role_code,
            statut_affectation_code=final_status.value,
            presence_confirmee=False,
        )
        return self.repo.create_assignment(new_affectation)

    def update_affectation_status(
        self, affectation_id: str, new_status: AffectationStatusCode
    ) -> Affectation:
        affectation = self.db.get(Affectation, affectation_id)
        if not affectation or not affectation.slot:
            raise AppException(ErrorRegistry.ASSIGNMENT_NOT_FOUND)

        # Règle métier croisée : Pointage possible uniquement si planning PUBLIE
        if new_status in [AffectationStatusCode.PRESENT, AffectationStatusCode.ABSENT]:
            planning = self.db.get(PlanningService, affectation.slot.planning_id)
            # Utilisation de la méthode de validation mutualisée
            if not planning:
                raise AppException(ErrorRegistry.ASSIGNMENT_PLANNING_PARENT_MISSING)
            self._validate_pointing_status(planning)

        current_status = AffectationStatusCode(affectation.statut_affectation_code)
        self.workflow.validate_transition(current_status, new_status)

        affectation.statut_affectation_code = new_status.value
        self.db.add(affectation)
        self.db.flush()
        return affectation

    def sync_assignments(self, slot_id: str, assignments_data: List[Any]):
        """Gère le delta (Add/Update/Delete) des affectations pour un slot."""
        db_affs = self.db.exec(
            select(Affectation).where(Affectation.slot_id == slot_id)
        ).all()
        current_map = {a.id: a for a in db_affs}

        payload_ids = {
            getattr(a, "id", None) for a in assignments_data if getattr(a, "id", None)
        }

        # 1. DELETE
        for a_id, aff_obj in current_map.items():
            if a_id not in payload_ids:
                self.db.delete(aff_obj)

        # 2. UPSERT
        for a_data in assignments_data:
            potential_id = getattr(a_data, "id", None)

            # Si l'ID existe et est connu en base -> UPDATE
            if isinstance(potential_id, str) and potential_id in current_map:
                status = getattr(a_data, "statut_affectation_code", None)
                if status:
                    self.update_affectation_status(
                        potential_id, AffectationStatusCode(status)
                    )

            # Sinon -> CREATE
            else:
                m_id: Any = getattr(a_data, "membre_id", None)
                r_code: Any = getattr(a_data, "role_code", None)

                raw_status = getattr(a_data, "statut_affectation_code", None) or (
                    a_data.get("statut_affectation_code")
                    if isinstance(a_data, dict)
                    else None
                )
                requested_status = (
                    AffectationStatusCode(raw_status) if raw_status else None
                )

                if isinstance(a_data, dict):
                    m_id = m_id or a_data.get("membre_id")
                    r_code = r_code or a_data.get("role_code")

                if isinstance(m_id, str) and isinstance(r_code, str):
                    self.assign_member_to_slot(
                        slot_id=slot_id,
                        membre_id=m_id,
                        role_code=r_code,
                        status=requested_status,
                    )
                else:
                    if not potential_id:
                        # Utilisation du registre pour le logging consistant
                        logger.warning(
                            ErrorRegistry.ASSIGNMENT_DATA_INCOMPLETE.message.format(
                                id=slot_id
                            )
                        )

    def delete_by_slot(self, slot_id: str) -> None:
        """Supprime toutes les affectations liées à un créneau."""
        db_affs = self.db.exec(
            select(Affectation).where(Affectation.slot_id == slot_id)
        ).all()
        for aff in db_affs:
            self.db.delete(aff)
        self.db.flush()
