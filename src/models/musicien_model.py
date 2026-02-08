import uuid
from typing import List, Optional

from pydantic import Field
from sqlmodel import SQLModel

from models.musicien_instrument_model import (
    MusicienInstrumentBase,
    MusicienInstrumentRead,
)


# -------------------------
# MUSICEN BASE
# -------------------------
class MusicienBase(SQLModel):
    chantre_id: uuid.UUID


class MusicienCreate(MusicienBase):
    # Liste des instruments à lier à la création
    instruments_in: List[MusicienInstrumentBase] = Field(default_factory=list)


class MusicienRead(MusicienBase):
    id: uuid.UUID
    # On renvoie la liste des liaisons
    # (qui contiennent l'ID de l'instrument et is_principal)
    instruments_assoc: List[MusicienInstrumentRead] = []

    @property
    def id_instrument_principal(self) -> Optional[uuid.UUID]:
        for item in self.instruments_assoc:
            if item.is_principal:
                return item.instrument_id
        return None


class MusicienUpdate(SQLModel):
    # Optionnel pour permettre de changer le chantre rattaché
    chantre_id: Optional[uuid.UUID] = None

    # Liste optionnelle pour mettre à jour les instruments
    # On utilise généralement la liste complète pour remplacer l'existante
    instruments_in: Optional[List[MusicienInstrumentBase]] = None

    model_config = {"from_attributes": True}


__all__ = ["MusicienBase", "MusicienCreate", "MusicienRead", "MusicienUpdate"]
