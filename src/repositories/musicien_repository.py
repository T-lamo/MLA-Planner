from typing import Any, cast

from sqlmodel import Session, select

from models import Musicien, MusicienInstrument
from repositories.base_repository import BaseRepository


class MusicienRepository(BaseRepository[Musicien]):
    def __init__(self, db: Session):
        super().__init__(db, Musicien)
        # On définit les relations à charger par défaut (Eager Loading)
        self.relations = [cast(Any, Musicien.instruments_assoc)]

    # --- Méthodes spécifiques ---
    def delete_instruments_by_musicien(self, musicien_id: Any):
        """Supprime techniquement les liaisons instruments."""
        statement = select(MusicienInstrument).where(
            MusicienInstrument.musicien_id == musicien_id
        )
        results = self.db.exec(statement).all()
        for r in results:
            self.db.delete(r)

    def add_instrument_link(
        self, musicien_id: Any, instrument_id: Any, is_principal: bool
    ):
        link = MusicienInstrument(
            musicien_id=musicien_id,
            instrument_id=instrument_id,
            is_principal=is_principal,
        )
        self.db.add(link)
