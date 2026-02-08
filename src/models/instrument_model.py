import uuid
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class InstrumentBase(SQLModel):
    # Le code est l'identifiant métier (ex: PIANO)
    code: str = Field(unique=True, index=True, max_length=20)
    # Le nom est le libellé affichable (ex: Piano Acoustique)
    nom: str = Field(max_length=50)


class InstrumentCreate(InstrumentBase):
    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str):
        return v.strip().upper().replace(" ", "_")


class InstrumentUpdate(SQLModel):
    code: Optional[str] = None
    nom: Optional[str] = None


class InstrumentRead(InstrumentBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


__all__ = ["InstrumentBase", "InstrumentCreate", "InstrumentUpdate", "InstrumentRead"]
