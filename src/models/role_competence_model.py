from typing import Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class RoleCompetenceBase(SQLModel):
    code: str = Field(
        primary_key=True, max_length=50, description="Code technique du rôle"
    )
    libelle: str = Field(max_length=100, description="Nom du rôle")
    categorie_code: str = Field(
        foreign_key="t_categorierole.code", description="Lien vers la catégorie parente"
    )

    @field_validator("code")
    @classmethod
    def clean_code(cls, v: str):
        return v.strip().upper()


# -------------------------
# CREATE
# -------------------------
class RoleCompetenceCreate(RoleCompetenceBase):
    pass


# -------------------------
# UPDATE
# -------------------------
class RoleCompetenceUpdate(SQLModel):
    libelle: Optional[str] = None
    categorie_code: Optional[str] = None


# -------------------------
# READ
# -------------------------
class RoleCompetenceRead(RoleCompetenceBase):
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = [
    "RoleCompetenceBase",
    "RoleCompetenceCreate",
    "RoleCompetenceUpdate",
    "RoleCompetenceRead",
]
