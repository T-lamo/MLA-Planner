from typing import Optional

from pydantic import computed_field, field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class MinistereBase(SQLModel):
    nom: str = Field(max_length=100, unique=True, index=True)
    date_creation: str
    actif: bool = True

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Le nom du ministère ne peut pas être vide")
        return v


# -------------------------
# CREATE
# -------------------------
class MinistereCreate(MinistereBase):
    campus_id: str


# -------------------------
# READ
# -------------------------
class MinistereRead(MinistereBase):
    id: str
    campus_id: str

    # SOLUTION POUR MYPY : Utiliser @computed_field seul (sans @property)
    # ou s'assurer qu'il est supporté. En Pydantic V2, @computed_field
    # est conçu pour décorer une property. L'erreur vient souvent de la
    # version de l'extension Mypy ou de l'ordre.
    # Alternative compatible Mypy :

    @computed_field  # type: ignore[misc]
    @property
    def poles_count(self) -> int:
        return len(getattr(self, "poles", []))

    @computed_field  # type: ignore[misc]
    @property
    def membres_count(self) -> int:
        return len(getattr(self, "membres", []))

    @computed_field  # type: ignore[misc]
    @property
    def equipes_count(self) -> int:
        return len(getattr(self, "equipes", []))


# -------------------------
# UPDATE
# -------------------------
class MinistereUpdate(SQLModel):
    nom: Optional[str] = None
    date_creation: Optional[str] = None
    actif: Optional[bool] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Le nom du ministère ne peut pas être vide")
        return v


# CRUCIAL : Ajouter "Ministere" ici pour que le Repository puisse l'importer !
__all__ = [
    "MinistereBase",
    "MinistereCreate",
    "MinistereRead",
    "MinistereUpdate",
]
