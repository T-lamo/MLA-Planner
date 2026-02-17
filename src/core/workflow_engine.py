# src/core/workflow_engine.py
import logging
from enum import Enum
from typing import Callable, Dict, Generic, List, Optional, TypeVar

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum.custom_enum import AffectationStatusCode, PlanningStatusCode

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Enum)


class WorkflowEngine(Generic[T]):
    def __init__(self, allowed_transitions: Dict[T, List[T]]):
        self.allowed_transitions = allowed_transitions

    def validate_transition(self, current_status: T, target_status: T):
        """
        Vérifie si la transition entre deux statuts est autorisée.
        Lève une AppException avec le code WKFL_001 si invalide.
        """
        # Conversion des valeurs pour la comparaison
        current_val = (
            current_status.value if hasattr(current_status, "value") else current_status
        )
        target_val = (
            target_status.value if hasattr(target_status, "value") else target_status
        )

        # Conversion des clés du dictionnaire de règles
        allowed_keys = {
            (k.value if hasattr(k, "value") else k): [
                (v.value if hasattr(v, "value") else v) for v in transitions
            ]
            for k, transitions in self.allowed_transitions.items()
        }

        if target_val not in allowed_keys.get(current_val, []):
            # Utilisation du registre centralisé pour l'erreur métier
            raise AppException(
                ErrorRegistry.WORKFLOW_INVALID_TRANSITION,
                current=current_val,
                target=target_val,
            )

    def execute_transition(
        self,
        current_status: T,
        target_status: T,
        hook: Optional[Callable[[], None]] = None,
    ):
        """Valide la transition et exécute un hook si fourni."""
        self.validate_transition(current_status, target_status)

        if hook:
            # Utilisation du registre pour le formatage des logs
            logger.info(
                ErrorRegistry.WORKFLOW_HOOK_EXECUTION.message.format(
                    current=current_status.value, target=target_status.value
                )
            )
            hook()

    def get_allowed_transitions(self, current_status: T) -> List[T]:
        """
        Retourne la liste des statuts vers lesquels le passage est autorisé
        à partir du statut actuel.
        """
        # 1. Normalisation du statut actuel (gère Enum ou str)
        current_val = (
            current_status.value if hasattr(current_status, "value") else current_status
        )

        # 2. Recherche dans le dictionnaire des transitions
        # On itère pour trouver la clé qui correspond à la valeur actuelle
        for status_enum, transitions in self.allowed_transitions.items():
            enum_val = (
                status_enum.value if hasattr(status_enum, "value") else status_enum
            )

            if enum_val == current_val:
                return transitions

        # Si aucune règle n'est définie pour ce statut, on retourne une liste vide
        logger.warning(
            f"Aucune règle de transition trouvée pour le statut: {current_val}"
        )
        return []


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
