from datetime import date
from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class OrganisationBase(SQLModel):
    nom: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=150,
        description="Nom officiel de l'organisation",
    )
    date_creation: date = Field(
        description="Date de création (format ISO ou texte, ex: 2020-01-01)"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="UUID de l'organisation parente (hiérarchie)",
    )

    @field_validator("nom")
    @classmethod
    def validate_nom(cls, v: str):
        if not v.strip():
            raise ValueError("Le nom de l'organisation ne peut pas être vide")
        return v.strip()


# -------------------------
# CREATE
# -------------------------
class OrganisationCreate(OrganisationBase):
    """
    Schéma pour la création : l'ID est généré automatiquement.
    """


# -------------------------
# UPDATE
# -------------------------
class OrganisationUpdate(SQLModel):
    nom: Optional[str] = None
    date_creation: Optional[date] = None
    parent_id: Optional[str] = None


# -------------------------
# READ
# -------------------------
class OrganisationRead(OrganisationBase):
    id: str
    date_creation: date
    parent_id: Optional[str] = None
    children: List["OrganisationRead"] = []


__all__ = [
    "OrganisationBase",
    "OrganisationUpdate",
    "OrganisationRead",
    "OrganisationCreate",
]
