from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from mla_enum import VoixEnum


# -------------------------
# BASE
# -------------------------
class VoixBase(SQLModel):
    code: VoixEnum = Field(index=True)
    nom: str = Field(max_length=100)
    description: Optional[str] = None
    active: bool = True

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("Le nom de la voix ne peut pas être vide")
        return v


# -------------------------
# CREATE
# -------------------------
class VoixCreate(VoixBase):
    pass


# -------------------------
# READ
# -------------------------
class VoixRead(VoixBase):
    code: VoixEnum
    choristes_count: Optional[int] = 0


# -------------------------
# UPDATE
# -------------------------
class VoixUpdate(SQLModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Le nom de la voix ne peut pas être vide")
        return v


__all__ = [
    "VoixBase",
    "VoixCreate",
    "VoixRead",
    "VoixUpdate",
]
