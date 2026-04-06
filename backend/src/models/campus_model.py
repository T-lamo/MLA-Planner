from typing import List, Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from .membre_model import MembreSimple
from .ministere_model import MinistereSimple


# -------------------------
# BASE
# -------------------------
class CampusBase(SQLModel):
    nom: str = Field(
        index=True, min_length=2, max_length=100, description="Nom du campus"
    )
    ville: str = Field(
        min_length=2, max_length=100, description="Ville où se situe le campus"
    )
    pays: Optional[str] = Field(
        default="France", max_length=100, description="Pays du campus"
    )
    timezone: str = Field(
        default="Europe/Paris", description="Fuseau horaire (ex: Africa/Abidjan)"
    )

    @field_validator("nom", "ville")
    @classmethod
    def not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip()


# -------------------------
# CREATE
# -------------------------
class CampusCreate(CampusBase):
    organisation_id: str = Field(
        max_length=36, description="UUID de l'organisation rattachée"
    )


# -------------------------
# UPDATE
# -------------------------
class CampusUpdate(SQLModel):
    nom: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    timezone: Optional[str] = None
    organisation_id: Optional[str] = None


# -------------------------
# READ
# -------------------------
class CampusRead(CampusBase):
    id: str
    organisation_id: str
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class CampusReadWithDetails(CampusRead):
    membres: List["MembreSimple"] = []
    ministeres: List["MinistereSimple"] = []


__all__ = [
    "CampusBase",
    "CampusUpdate",
    "CampusRead",
    "CampusCreate",
    "CampusReadWithDetails",
]
