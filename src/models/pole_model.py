from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from models import MinistereRead


# -------------------------
# BASE
# -------------------------
class PoleBase(SQLModel):
    nom: str = Field(max_length=100)
    description: Optional[str] = None
    active: bool = True

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("Le nom du pôle ne peut pas être vide")
        return v


# -------------------------
# CREATE
# -------------------------
class PoleCreate(PoleBase):
    ministere_id: str  # obligatoire pour créer un pôle


# -------------------------
# READ
# -------------------------
class PoleRead(PoleBase):
    id: str
    ministere: Optional["MinistereRead"] = None
    membres_count: Optional[int] = 0


# -------------------------
# UPDATE
# -------------------------
class PoleUpdate(SQLModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    ministere_id: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Le nom du pôle ne peut pas être vide")
        return v


__all__ = [
    "PoleBase",
    "PoleCreate",
    "PoleRead",
    "PoleUpdate",
]
