# Utilisation d'annotations différées pour éviter les cycles d'import
from __future__ import annotations

from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from utils.validator import NotBlankFieldsMixin

from .membre_model import MembreRead


# -------------------------
# BASE
# -------------------------
class PoleBase(NotBlankFieldsMixin, SQLModel):
    __not_blank_fields__ = ("nom",)

    # On ajoute la contrainte de longueur directement dans le type pour Pydantic
    nom: str = Field(index=True, max_length=100, description="Nom unique du pôle")
    description: Optional[str] = Field(default=None, max_length=500)
    active: bool = Field(default=True)

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str) -> str:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Le nom du pôle ne peut pas être vide")
        return v


# -------------------------
# CREATE
# -------------------------
class PoleCreate(PoleBase):
    ministere_id: str


# -------------------------
# READ (Version Allégée - Pour inclusion dans Profil/Ministère)
# -------------------------
class PoleRead(PoleBase):
    """
    Schéma de lecture simple sans relations profondes.
    Utilisé pour alléger le JSON global.
    """

    id: str
    ministere_id: str
    # On retire la liste des membres ici pour éviter la récursion
    membres_count: int = 0

    model_config = {"from_attributes": True}


# -------------------------
# READ WITH RELATIONS (Version Riche - Pour endpoint dédié)
# -------------------------
class PoleReadWithMembres(PoleRead):
    """
    Utilisé uniquement quand on veut spécifiquement les membres d'un pôle.
    """

    poles_membres: List["MembreRead"] = Field(default=[], alias="membres")


# -------------------------
# UPDATE
# -------------------------
class PoleUpdate(NotBlankFieldsMixin, SQLModel):
    __not_blank_fields__ = ("nom",)

    nom: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    ministere_id: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str) -> str:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Le nom du pôle ne peut pas être vide")
        return v


__all__ = [
    "PoleBase",
    "PoleCreate",
    "PoleRead",
    "PoleReadWithMembres",
    "PoleUpdate",
]
