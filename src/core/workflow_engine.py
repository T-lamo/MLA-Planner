# src/core/workflow_engine.py
import logging
from enum import Enum
from typing import Callable, Dict, Generic, List, Optional, TypeVar

from core.exceptions import BadRequestException
from mla_enum.custom_enum import AffectationStatusCode, PlanningStatusCode

logger = logging.getLogger(__name__)


class WorkflowError(BadRequestException):
    """Exception levée lors d'une transition de statut invalide."""


T = TypeVar("T", bound=Enum)


class WorkflowEngine(Generic[T]):
    def __init__(self, allowed_transitions: Dict[T, List[T]]):
        self.allowed_transitions = allowed_transitions

    def validate_transition(self, current_status: T, target_status: T):
        # --- CORRECTION ICI ---
        # On convertit les valeurs pour être sûr de comparer des strings (les .value)

        current_val = (
            current_status.value if hasattr(current_status, "value") else current_status
        )
        target_val = (
            target_status.value if hasattr(target_status, "value") else target_status
        )

        # On convertit aussi les clés du dictionnaire pour la comparaison
        allowed_keys = {
            (k.value if hasattr(k, "value") else k): [
                (v.value if hasattr(v, "value") else v) for v in transitions
            ]
            for k, transitions in self.allowed_transitions.items()
        }

        if target_val not in allowed_keys.get(current_val, []):
            raise WorkflowError(f"Transition impossible: {current_val} -> {target_val}")

    def execute_transition(
        self,
        current_status: T,  # Changé de Enum à T
        target_status: T,  # Changé de Enum à T
        hook: Optional[Callable[[], None]] = None,
    ):
        """Valide la transition et exécute un hook si fourni."""
        self.validate_transition(current_status, target_status)

        if hook:
            logger.info(
                f"Exécution du hook pour transition {current_status.value} -> {target_status.value}"
            )
            hook()


# --- Définition des règles métier ---

# Planning : BROUILLON, PUBLIE, ANNULE, TERMINE
planning_transitions: dict[PlanningStatusCode, list[PlanningStatusCode]] = {
    PlanningStatusCode.BROUILLON: [
        PlanningStatusCode.PUBLIE,
        PlanningStatusCode.ANNULE,
    ],
    PlanningStatusCode.PUBLIE: [PlanningStatusCode.TERMINE, PlanningStatusCode.ANNULE],
    PlanningStatusCode.ANNULE: [PlanningStatusCode.BROUILLON],
    PlanningStatusCode.TERMINE: [],
}

# Affectation : PROPOSE, CONFIRME, REFUSE, PRESENT, ABSENT
affectation_transitions: Dict[AffectationStatusCode, List[AffectationStatusCode]] = {
    AffectationStatusCode.PROPOSE: [
        AffectationStatusCode.CONFIRME,
        AffectationStatusCode.REFUSE,
    ],
    AffectationStatusCode.CONFIRME: [
        AffectationStatusCode.PRESENT,
        AffectationStatusCode.ABSENT,
        AffectationStatusCode.REFUSE,
    ],
    AffectationStatusCode.REFUSE: [AffectationStatusCode.PROPOSE],
    AffectationStatusCode.PRESENT: [AffectationStatusCode.CONFIRME],
    AffectationStatusCode.ABSENT: [AffectationStatusCode.CONFIRME],
}
