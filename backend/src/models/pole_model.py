# Utilisation d'annotations différées pour éviter les cycles d'import
from __future__ import annotations

from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel
from utils.validator import NotBlankFieldsMixin


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
# READ
# -------------------------
class PoleRead(PoleBase):
    id: str
    # ministere_id reste présent pour le front-end
    ministere_id: str
    membres_count: int = 0


# -------------------------
# UPDATE
# -------------------------
# On hérite de SQLModel directement mais on peut réutiliser la validation de Base
class PoleUpdate(NotBlankFieldsMixin, SQLModel):
    __not_blank_fields__ = ("nom",)

    nom: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    ministere_id: Optional[str] = None

    # On réutilise le validateur de la classe de base
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
    "PoleUpdate",
]

PoleRead.model_rebuild()
