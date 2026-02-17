# src/repositories/indisponibilite_repository.py
from typing import List

from models import Indisponibilite
from repositories.base_repository import BaseRepository
from sqlmodel import Session, select


class IndisponibiliteRepository(BaseRepository[Indisponibilite]):
    """Repository spécifique pour gérer les indisponibilités des membres."""

    def __init__(self, db: Session):
        # On passe le modèle Indisponibilite à la classe parente
        super().__init__(db, Indisponibilite)

    def get_by_membre(self, membre_id: str) -> List[Indisponibilite]:
        """Récupère toutes les indisponibilités d'un membre spécifique."""
        statement = select(Indisponibilite).where(
            Indisponibilite.membre_id == membre_id
        )
        return list(self.db.exec(statement).all())
