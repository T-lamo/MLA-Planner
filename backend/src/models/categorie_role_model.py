from typing import Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Imports pour la centralisation des erreurs
from core.message import ErrorRegistry

from .role_competence_model import RoleCompetenceRead


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

    # Lien vers le ministère parent (ajouté pour Campus Configuration)
    # Migration requise :
    # ALTER TABLE t_categorierole
    #   ADD COLUMN ministere_id VARCHAR
    #   REFERENCES t_ministere(id) ON DELETE SET NULL;
    ministere_id: Optional[str] = Field(
        default=None,
        foreign_key="t_ministere.id",
        description="UUID du ministère parent (Campus Config)",
    )

    # Champ description optionnel (ajouté pour Campus Configuration)
    # Migration requise :
    # ALTER TABLE t_categorierole ADD COLUMN description TEXT;
    description: Optional[str] = Field(
        default=None,
        description="Description libre de la catégorie",
    )

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


class RoleWithCategoryRead(RoleCompetenceRead):
    """Extension de RoleCompetenceRead pour inclure la catégorie chargée."""

    categorie: Optional[CategorieRoleRead] = None


__all__ = [
    "CategorieRoleBase",
    "CategorieRoleCreate",
    "CategorieRoleUpdate",
    "CategorieRoleRead",
    "RoleWithCategoryRead",
]
