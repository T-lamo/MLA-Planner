from typing import List, Optional

from models.campus_model import CampusRead
from pydantic import field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class PaysBase(SQLModel):
    nom: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=100,
        description="Nom complet du pays (ex: Côte d'Ivoire)",
    )
    code: str = Field(
        index=True,
        min_length=2,
        max_length=5,
        description="Code ISO ou interne du pays (ex: CI, FR, BE)",
    )

    @field_validator("nom", "code")
    @classmethod
    def validate_strings(cls, v: str):
        if not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip()

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, v: str):
        return v.upper()


# -------------------------
# CREATE
# -------------------------
class PaysCreate(PaysBase):
    organisation_id: str = Field(
        max_length=36, description="UUID de l'organisation ICC parente"
    )


# -------------------------
# UPDATE
# -------------------------
class PaysUpdate(SQLModel):
    nom: Optional[str] = None
    code: Optional[str] = None
    organisation_id: Optional[str] = None


# -------------------------
# READ
# -------------------------
class PaysRead(PaysBase):
    id: str
    organisation_id: str
    # On peut ajouter le compte des campus pour les statistiques
    campus: List[CampusRead]


__all__ = ["PaysBase", "PaysUpdate", "PaysRead", "PaysCreate"]
