import logging

from sqlmodel import Session

from core.exceptions.exceptions import BadRequestException
from core.workflow_engine import WorkflowEngine, affectation_transitions
from mla_enum.custom_enum import AffectationStatusCode, PlanningStatusCode
from models import Affectation
from models.schema_db_model import PlanningService
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
        self, slot_id: str, membre_id: str, role_code: str
    ) -> Affectation:
        """Orchestre la validation et la création de l'affectation."""

        logger.info(
            f"Tentative d'affectation : Membre {membre_id} "
            f"sur Slot {slot_id} en tant que {role_code}"
        )

        # 1. Validation métier (Le moteur lève des exceptions si KO)
        self.validator.validate_member_for_slot(self.db, membre_id, slot_id, role_code)

        # 2. Création de l'affectation dans une transaction atomique
        try:
            with self.db.begin_nested():
                new_affectation = Affectation(
                    slot_id=slot_id,
                    membre_id=membre_id,
                    role_code=role_code,
                    statut_affectation_code=AffectationStatusCode.PROPOSE.value,
                    presence_confirmee=False,
                )
                result = self.repo.create_assignment(new_affectation)

            logger.info(f"Affectation réussie : ID {result.id}")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'affectation : {str(e)}")
            raise e

    def update_affectation_status(
        self, affectation_id: str, new_status: AffectationStatusCode
    ) -> Affectation:
        # 1. Récupération avec vérification de présence (Fix mypy None)
        affectation = self.db.get(Affectation, affectation_id)
        if not affectation:
            raise BadRequestException(f"Affectation {affectation_id} introuvable.")

        # Accès sécurisé à slot via l'objet validé
        if not affectation.slot:
            raise BadRequestException("L'affectation n'est liée à aucun créneau.")

        planning = self.db.get(PlanningService, affectation.slot.planning_id)
        if not planning:
            raise BadRequestException("Planning introuvable pour cette affectation.")

        # 2. Règle métier croisée
        if new_status in [AffectationStatusCode.PRESENT, AffectationStatusCode.ABSENT]:
            if planning.statut_code != PlanningStatusCode.PUBLIE.value:
                raise BadRequestException(
                    "Impossible de pointer une présence sur un planning non publié."
                )

        try:
            # On utilise flush pour rester dans la transaction atomique
            current_status = AffectationStatusCode(affectation.statut_affectation_code)
            self.workflow.validate_transition(current_status, new_status)

            affectation.statut_affectation_code = new_status.value
            self.db.add(affectation)
            self.db.commit()
            self.db.refresh(affectation)
            return affectation
        except Exception as e:
            self.db.rollback()
            raise e
