from datetime import datetime
from typing import Optional

from pydantic import model_validator
from sqlmodel import Field, SQLModel


class SlotBase(SQLModel):
    planning_id: str = Field(foreign_key="t_planningservice.id", ondelete="CASCADE")
    nom_creneau: str = Field(max_length=100)
    date_debut: datetime
    date_fin: datetime
    nb_personnes_requis: int = Field(default=2, ge=1)


class SlotUpdate(SQLModel):
    nom_creneau: Optional[str] = Field(default=None, max_length=100)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None


class SlotCreate(SlotBase):
    @model_validator(mode="after")
    def validate_chronology(self):
        if self.date_fin <= self.date_debut:
            raise ValueError(
                "La date de fin doit être strictement supérieure à la date de début"
            )
        return self


class SlotRead(SlotBase):
    id: str


__all__ = [
    "SlotBase",
    "SlotCreate",
    "SlotRead",
    "SlotUpdate",
]
