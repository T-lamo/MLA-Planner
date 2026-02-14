from sqlmodel import Session

from core.exceptions import BadRequestException, NotFoundException
from core.exceptions.exceptions import ConflictException
from models.slot_model import SlotCreate
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

    @staticmethod
    def validate_slot_timing(
        _db: Session, slot_create: SlotCreate, repo: PlanningRepository
    ):
        # AC4 : Intégrité référentielle
        planning = repo.get_planning_with_activity(slot_create.planning_id)
        if not planning:
            raise NotFoundException(f"Planning {slot_create.planning_id} non trouvé.")

        # AC1 : Parentalité temporelle
        activity = planning.activite
        if (
            slot_create.date_debut < activity.date_debut
            or slot_create.date_fin > activity.date_fin
        ):
            raise BadRequestException(
                f"Le slot doit être compris entre"
                f"{activity.date_debut} et {activity.date_fin}"
            )

        # AC3 : Détection de collision
        existing_slots = repo.get_slots_by_planning(slot_create.planning_id)
        collision = None

        for existing in existing_slots:
            # Formule : (Start1 < End2) AND (End1 > Start2)
            if (
                slot_create.date_debut < existing.date_fin
                and slot_create.date_fin > existing.date_debut
            ):
                collision = existing  # On stocke le slot qui cause le conflit
                break  # On arrête la boucle dès qu'un conflit est trouvé

        if collision:
            raise ConflictException(
                f"Collision avec le slot existant '{collision.nom_creneau}' "
                f"({collision.date_debut} - {collision.date_fin})"
            )
