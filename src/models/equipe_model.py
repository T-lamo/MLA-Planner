from typing import List, Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Importation du registre et de AppException
from core.message import ErrorRegistry
from models.equipe_membre import EquipeMembreRead

# -------------------------
# 2. SCHÉMAS Pydantic (DTOs)
# -------------------------


# --- BASE ---
class EquipeBase(SQLModel):
    nom: str = Field(max_length=100, description="Nom de l'équipe")
    active: bool = Field(default=True, description="Statut de l'équipe")

    @field_validator("nom")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            # Utilisation de AppException au lieu de ValueError
            raise AppException(ErrorRegistry.TEAM_NAME_EMPTY)
        return v.strip()


# --- CREATE ---
class EquipeCreate(EquipeBase):
    """Schéma pour la création d'une équipe, nécessite un ministere_id."""

    ministere_id: str = Field(description="UUID du ministère de rattachement")


# --- UPDATE ---
class EquipeUpdate(SQLModel):
    """Schéma pour la mise à jour, tous les champs sont optionnels."""

    nom: Optional[str] = Field(default=None, max_length=100)
    active: Optional[bool] = None
    ministere_id: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise AppException(ErrorRegistry.TEAM_NAME_EMPTY)
        return v.strip() if v else None


# --- READ ---
class EquipeRead(EquipeBase):
    """Schéma de réponse API standard."""

    id: str
    ministere_id: str
    membres_assoc: List[EquipeMembreRead] = []

    # Configuration cruciale pour la sérialisation ORM
    model_config = ConfigDict(from_attributes=True)  # type: ignore


# -------------------------
# 3. EXPORTS
# -------------------------
__all__ = [
    "EquipeBase",
    "EquipeCreate",
    "EquipeUpdate",
    "EquipeRead",
]
