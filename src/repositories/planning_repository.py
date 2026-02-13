# src/repositories/planning_repository.py
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from models import Activite, PlanningService

from .base_repository import BaseRepository


class PlanningRepository(BaseRepository[PlanningService]):
    def __init__(self, db: Session):
        super().__init__(db, PlanningService)

    def get_by_campus(self, campus_id: str):
        """Récupère les plannings via une jointure sur l'activité."""
        statement = (
            select(self.model).join(Activite).where(Activite.campus_id == campus_id)
        )
        return self.db.exec(statement).all()

    def get_with_slots(self, planning_id: str) -> Optional[PlanningService]:
        """Récupère un planning avec tous ses slots chargés (Eager Loading)."""
        statement = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(selectinload(PlanningService.slots))  # type: ignore
        )
        return self.db.exec(statement).unique().first()
