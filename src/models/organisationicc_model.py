from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class OrganisationICCBase(SQLModel):
    nom: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=150,
        description="Nom officiel de l'organisation",
    )
    dateCreation: str = Field(
        description="Date de création (format ISO ou texte, ex: 2020-01-01)"
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
class OrganisationICCCreate(OrganisationICCBase):
    """
    Schéma pour la création : l'ID est généré automatiquement.
    """


# -------------------------
# UPDATE
# -------------------------
class OrganisationICCUpdate(SQLModel):
    nom: Optional[str] = None
    dateCreation: Optional[str] = None


# -------------------------
# READ
# -------------------------
class OrganisationICCRead(OrganisationICCBase):
    id: str
    # Optionnel: on peut inclure le nombre de pays rattachés
    pays_count: Optional[int] = 0


__all__ = [
    "OrganisationICCBase",
    "OrganisationICCUpdate",
    "OrganisationICCRead",
    "OrganisationICCCreate",
]
