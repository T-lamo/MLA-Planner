from datetime import date
from typing import List, Optional

from pydantic import field_validator
from sqlmodel import SQLModel

from .affectation_context_model import AffectationContexteRead


# -------------------------
# BASE
# -------------------------
class AffectationRoleBase(SQLModel):
    dateDebut: Optional[date] = None
    dateFin: Optional[date] = None
    active: bool = True

    @field_validator("dateFin")
    @classmethod
    def check_dates(cls, v, info):
        data = info.data
        start = data.get("dateDebut")

        if v and start and v < start:
            raise ValueError("dateFin ne peut pas être antérieure à dateDebut")
        return v


# -------------------------
# CREATE
# -------------------------
class AffectationRoleCreate(AffectationRoleBase):
    utilisateur_id: str
    role_id: str
    contextes_ids: Optional[List[str]] = []

    @field_validator("utilisateur_id", "role_id")
    @classmethod
    def not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("Les identifiants ne peuvent pas être vides")
        return v


# -------------------------
# READ
# -------------------------
class AffectationRoleRead(AffectationRoleBase):
    id: str
    utilisateur_id: str
    role_id: str
    contextes: List["AffectationContexteRead"] = []


# -------------------------
# UPDATE
# -------------------------
class AffectationRoleUpdate(SQLModel):
    dateDebut: Optional[date] = None
    dateFin: Optional[date] = None
    active: Optional[bool] = None
    role_id: Optional[str] = None
    contextes_ids: Optional[List[str]] = None

    @field_validator("dateFin")
    @classmethod
    def validate_dates(cls, v, info):
        data = info.data
        start = data.get("dateDebut")

        if v and start and v < start:
            raise ValueError("dateFin ne peut pas être antérieure à dateDebut")
        return v


__all__ = [
    "AffectationRoleBase",
    "AffectationRoleUpdate",
    "AffectationRoleRead",
    "AffectationRoleCreate",
]
