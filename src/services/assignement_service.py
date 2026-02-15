import logging
from typing import Any, List, Optional

from sqlmodel import Session, select

from core.exceptions.exceptions import BadRequestException
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
                raise BadRequestException(f"Slot {slot_id} introuvable.")

            planning = self.db.get(PlanningService, slot.planning_id)
            if not planning:
                raise BadRequestException("Planning introuvable pour ce créneau.")

            if planning.statut_code != PlanningStatusCode.PUBLIE.value:
                raise BadRequestException(
                    "Impossible de pointer sur un planning non publié."
                )

        # ATTENTION : Correction ici aussi pour utiliser final_status.value
        # Sinon ton affectation sera créée en PROPOSE même si tu as passé PRESENT
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
            raise BadRequestException("Affectation ou slot introuvable.")

        # Règle métier croisée : Pointage possible uniquement si planning PUBLIE
        planning = self.db.get(PlanningService, affectation.slot.planning_id)
        if not planning:
            raise BadRequestException(
                "Planning parent introuvable pour cette affectation."
            )
        if new_status in [AffectationStatusCode.PRESENT, AffectationStatusCode.ABSENT]:
            if planning.statut_code != PlanningStatusCode.PUBLIE.value:
                raise BadRequestException(
                    "Impossible de pointer sur un planning non publié."
                )

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

        # On collecte les IDs présents dans le payload
        payload_ids = {
            getattr(a, "id", None) for a in assignments_data if getattr(a, "id", None)
        }

        # 1. DELETE
        for a_id, aff_obj in current_map.items():
            if a_id not in payload_ids:
                self.db.delete(aff_obj)

        # 2. UPSERT
        for a_data in assignments_data:
            # On récupère l'ID et on force la vérification de type pour Mypy
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
                # --- CORRECTION ICI : On récupère le statut demandé ---
                raw_status = getattr(a_data, "statut_affectation_code", None) or (
                    a_data.get("statut_affectation_code")
                    if isinstance(a_data, dict)
                    else None
                )
                requested_status = (
                    AffectationStatusCode(raw_status) if raw_status else None
                )
                # ------------------------------------------------------

                if isinstance(a_data, dict):
                    m_id = m_id or a_data.get("membre_id")
                    r_code = r_code or a_data.get("role_code")

                # Type Guard : m_id et r_code DOIVENT être str
                if isinstance(m_id, str) and isinstance(r_code, str):
                    self.assign_member_to_slot(
                        slot_id=slot_id,
                        membre_id=m_id,
                        role_code=r_code,
                        status=requested_status,
                    )
                else:
                    # On ne logue que si on n'est pas dans le cas d'un
                    # update (potential_id présent)
                    if not potential_id:
                        logger.warning(
                            f"Données d'affectation incomplètes pour le slot {slot_id}"
                        )
