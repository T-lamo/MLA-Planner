from sqlmodel import Session

from core.exceptions import BadRequestException, NotFoundException
from repositories.planning_repository import PlanningRepository


class ValidationEngine:
    @staticmethod
    def validate_member_for_slot(
        db: Session, membre_id: str, slot_id: str, role_code: str
    ) -> bool:
        """
        Vérifie si le membre est éligible pour le slot selon son rôle.
        Retourne True si valide, lève une exception sinon.
        """
        repo = PlanningRepository(db)

        # 1. Vérifier si le slot existe
        slot = repo.get_slot_with_relations(slot_id)
        if not slot:
            raise NotFoundException(f"Slot {slot_id} introuvable.")

        # 2. Vérifier la compétence (rôle)
        has_role = repo.check_member_has_role(membre_id, role_code)

        if not has_role:
            # On lève une exception métier ici plutôt que de retourner False
            # pour donner un contexte précis à l'utilisateur.
            raise BadRequestException(
                f"Le membre ne possède pas le rôle requis : {role_code}"
            )

        return True
