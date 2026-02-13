from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SlotBase(SQLModel):
    planning_id: str = Field(foreign_key="t_planningservice.id", ondelete="CASCADE")
    nom_creneau: str = Field(max_length=100)
    date_debut: datetime
    date_fin: datetime


class SlotUpdate(SQLModel):
    nom_creneau: Optional[str] = Field(default=None, max_length=100)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None


class SlotCreate(SlotBase):
    pass


class SlotRead(SlotBase):
    id: str


__all__ = [
    "SlotBase",
    "SlotCreate",
    "SlotRead",
    "SlotUpdate",
]
