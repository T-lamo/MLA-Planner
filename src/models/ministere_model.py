from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class MinistereBase(SQLModel):
    nom: str = Field(max_length=100)
    date_creation: str
    actif: bool = True

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("Le nom du ministère ne peut pas être vide")
        return v


# -------------------------
# CREATE
# -------------------------
class MinistereCreate(MinistereBase):
    campus_id: str  # obligatoire pour créer un ministère


# -------------------------
# READ
# -------------------------
class MinistereRead(MinistereBase):
    id: str
    # campus: Optional[CampusRead] = None
    poles_count: Optional[int] = 0
    membres_count: Optional[int] = 0
    equipes_count: Optional[int] = 0


# -------------------------
# UPDATE
# -------------------------
class MinistereUpdate(SQLModel):
    nom: Optional[str] = None
    date_creation: Optional[str] = None
    actif: Optional[bool] = None
    # campus_id: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Le nom du ministère ne peut pas être vide")
        return v


__all__ = [
    "MinistereBase",
    "MinistereCreate",
    "MinistereRead",
    "MinistereUpdate",
]
