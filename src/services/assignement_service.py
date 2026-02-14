import logging

from sqlmodel import Session

from mla_enum.custom_enum import AffectationStatusCode
from models import Affectation
from repositories.planning_repository import PlanningRepository
from services.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PlanningRepository(db)
        self.validator = ValidationEngine()

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
