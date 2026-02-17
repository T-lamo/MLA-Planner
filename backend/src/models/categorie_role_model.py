from typing import Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Imports pour la centralisation des erreurs
from core.message import ErrorRegistry


# -------------------------
# BASE
# -------------------------
class CategorieRoleBase(SQLModel):
    code: str = Field(
        primary_key=True,
        max_length=20,
        description="Code unique de la catégorie (ex: TECH, ADMIN)",
    )
    libelle: str = Field(max_length=100, description="Libellé complet de la catégorie")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str):
        v = v.strip().upper()
        # Utilisation de la logique alphanumérique avec underscores
        if not v.isalnum() and "_" not in v:
            # Remplacement de ValueError par AppException avec le registre
            raise AppException(ErrorRegistry.ROLE_CAT_INVALID_CODE)
        return v


# -------------------------
# CREATE
# -------------------------
class CategorieRoleCreate(CategorieRoleBase):
    pass  # Le code est fourni manuellement car c'est une PK naturelle


# -------------------------
# UPDATE
# -------------------------
class CategorieRoleUpdate(SQLModel):
    libelle: Optional[str] = None


# -------------------------
# READ
# -------------------------
class CategorieRoleRead(CategorieRoleBase):
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = [
    "CategorieRoleBase",
    "CategorieRoleCreate",
    "CategorieRoleUpdate",
    "CategorieRoleRead",
]
