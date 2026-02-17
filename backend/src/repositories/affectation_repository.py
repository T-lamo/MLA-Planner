from datetime import datetime

from sqlmodel import Session, select

from models import Affectation, Slot
from repositories.base_repository import BaseRepository


class AffectationRepository(BaseRepository[Affectation]):
    def __init__(self, db: Session):
        super().__init__(db, Affectation)

    def check_overlap(
        self, membre_id: str, date_debut: datetime, date_fin: datetime
    ) -> bool:
        """Vérifie si le membre est déjà affecté à un autre slot sur la même période."""
        statement = (
            select(Affectation)
            .join(Slot)
            .where(
                Affectation.membre_id == membre_id,
                Slot.date_debut < date_fin,
                Slot.date_fin > date_debut,
            )
        )
        results = self.db.exec(statement).all()
        return len(results) > 0
