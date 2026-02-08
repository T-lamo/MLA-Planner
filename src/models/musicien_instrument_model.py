import uuid
from typing import Optional

from sqlmodel import Field, SQLModel

from models.instrument_model import InstrumentRead


# -------------------------
# MUSICEN-INSTRUMENT BASE
# -------------------------
class MusicienInstrumentBase(SQLModel):
    instrument_id: uuid.UUID = Field(
        foreign_key="t_instrument.id", primary_key=True, ondelete="CASCADE"
    )
    is_principal: bool = Field(default=False)


# --- CREATE / READ ---
class MusicienInstrumentCreate(MusicienInstrumentBase):
    musicien_id: uuid.UUID = Field(foreign_key="t_musicien.id", primary_key=True)


class MusicienInstrumentRead(MusicienInstrumentBase):
    musicien_id: uuid.UUID
    # Optionnel : inclure le code de l'instrument pour faciliter la lecture front
    instrument: Optional[InstrumentRead] = None


__all__ = [
    "MusicienInstrumentBase",
    "MusicienInstrumentCreate",
    "MusicienInstrumentRead",
]
