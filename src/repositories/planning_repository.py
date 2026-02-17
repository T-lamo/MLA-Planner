# src/repositories/planning_repository.py
from typing import Optional

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, and_, select

from models import Activite, PlanningService
from models.schema_db_model import Affectation, MembreRole, Slot

from .base_repository import BaseRepository


class PlanningRepository(BaseRepository[PlanningService]):
    def __init__(self, db: Session):
        super().__init__(db, PlanningService)

    def get_by_campus(self, campus_id: str):
        statement = (
            select(PlanningService)
            .join(Activite)
            .where(Activite.campus_id == campus_id)
        )
        return self.db.exec(statement).all()

    def get_with_slots(self, planning_id: str) -> Optional[PlanningService]:
        """Récupère un planning avec tous ses slots chargés."""
        statement = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(selectinload(PlanningService.slots))  # type: ignore
        )
        return self.db.exec(statement).unique().first()

    def get_slot_with_relations(self, slot_id: str) -> Optional[Slot]:
        """
        Récupère un slot avec son planning ET l'activité liée.
        Correction Mypy : Utilisation des attributs de classe.
        """
        statement = (
            select(Slot)
            .where(Slot.id == slot_id)
            .options(
                joinedload(Slot.planning).joinedload(  # type: ignore
                    PlanningService.activite  # type: ignore
                )  # type: ignore
            )
        )
        # Note: Si Mypy râle encore sur le chaînage, on utilise le type ignore
        # car SQLModel masque parfois les attributs SQLAlchemy sous-jacents.
        return self.db.exec(statement).unique().first()  # type: ignore

    def check_member_has_role(self, membre_id: str, role_code: str) -> bool:
        statement = select(MembreRole).where(
            and_(MembreRole.membre_id == membre_id, MembreRole.role_code == role_code)
        )
        result = self.db.exec(statement).first()
        return result is not None

    def create_affectation(self, affectation: Affectation) -> Affectation:
        self.db.add(affectation)
        # self.db.flush()
        # self.db.refresh(affectation)
        return affectation

    def get_planning_with_activity(self, planning_id: str):
        """Récupère le planning et son activité parente (évite N+1)."""
        return self.db.exec(
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(selectinload(PlanningService.activite))  # type: ignore
        ).first()

    def get_slots_by_planning(self, planning_id: str):
        """Récupère tous les slots d'un planning pour vérifier les collisions."""
        return self.db.exec(select(Slot).where(Slot.planning_id == planning_id)).all()

    def save_slot(self, slot: Slot) -> Slot:
        self.db.add(slot)
        return slot
