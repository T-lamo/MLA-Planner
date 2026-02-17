# src/services/validation_engine.py
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models.slot_model import SlotCreate
from repositories.planning_repository import PlanningRepository
from sqlmodel import Session


class ValidationEngine:
    @staticmethod
    def validate_member_for_slot(
        db: Session, membre_id: str, slot_id: str, role_code: str
    ) -> bool:
        """
        Vérifie si le membre est éligible pour le slot selon son rôle.
        Retourne True si valide, lève une AppException sinon.
        """
        repo = PlanningRepository(db)

        # 1. Vérifier si le slot existe (Utilisation du code contextuel ASGN)
        slot = repo.get_slot_with_relations(slot_id)
        if not slot:
            raise AppException(ErrorRegistry.ASGN_SLOT_NOT_FOUND, id=slot_id)

        # 2. Vérifier la compétence (rôle)
        has_role = repo.check_member_has_role(membre_id, role_code)

        if not has_role:
            # Remplacement par la constante typée membre/rôle
            raise AppException(ErrorRegistry.ASGN_MEMBER_MISSING_ROLE, role=role_code)

        return True

    @staticmethod
    def validate_slot_timing(
        _db: Session, slot_create: SlotCreate, repo: PlanningRepository
    ):
        """Valide les contraintes temporelles et l'intégrité du planning."""

        # AC4 : Intégrité référentielle
        planning = repo.get_planning_with_activity(slot_create.planning_id)
        if not planning:
            raise AppException(
                ErrorRegistry.VALIDATION_PLANNING_NOT_FOUND, id=slot_create.planning_id
            )

        # AC1 : Parentalité temporelle
        activity = planning.activite
        if (
            slot_create.date_debut < activity.date_debut
            or slot_create.date_fin > activity.date_fin
        ):
            raise AppException(
                ErrorRegistry.VALIDATION_SLOT_OUT_OF_RANGE,
                debut=activity.date_debut,
                fin=activity.date_fin,
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
                collision = existing
                break

        if collision:
            raise AppException(
                ErrorRegistry.VALIDATION_SLOT_COLLISION_DETAIL,
                nom=collision.nom_creneau,
                debut=collision.date_debut,
                fin=collision.date_fin,
            )
