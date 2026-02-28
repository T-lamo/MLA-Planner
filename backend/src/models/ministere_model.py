from typing import List, Optional

from pydantic import computed_field, field_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Importation du registre et de l'AppException
from core.message import ErrorRegistry
from models.membre_model import MembreRead

from .pole_model import PoleRead


# -------------------------
# BASE
# -------------------------
class MinistereBase(SQLModel):
    nom: str = Field(max_length=100, unique=True, index=True)
    date_creation: str  # Format ISO YYYY-MM-DD
    actif: bool = True

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise AppException(ErrorRegistry.MINST_NAME_EMPTY)
        return v


# -------------------------
# CREATE
# -------------------------
class MinistereCreate(MinistereBase):
    campus_ids: List[str] = []


# -------------------------
# READ (Version Allégée - Utilisée dans ProfilReadFull)
# -------------------------
class MinistereRead(MinistereBase):
    """
    Version optimisée pour l'inclusion dans d'autres objets.
    Incorpore les Pôles (déjà allégés) mais EXCLUT la liste des membres.
    """

    id: str
    # On inclut les pôles car ils sont "petits" (PoleRead ne contient plus de membres)
    model_config = {"from_attributes": True}


# -------------------------
# READ WITH RELATIONS (Version Riche - Utilisée pour l'admin/détail)
# -------------------------
class MinistereReadWithRelations(MinistereRead):
    """
    Version complète incluant la liste des membres rattachés.
    """

    ministeres_membres: List["MembreRead"] = Field(default=[], alias="membres")
    poles: List[PoleRead] = []

    @computed_field
    def membres_count(self) -> int:
        return len(self.ministeres_membres) if self.ministeres_membres else 0

    @computed_field
    def poles_count(self) -> int:
        return len(self.poles) if self.poles else 0


# -------------------------
# UPDATE
# -------------------------
class MinistereUpdate(SQLModel):
    nom: Optional[str] = None
    date_creation: Optional[str] = None
    actif: Optional[bool] = None
    campus_ids: Optional[List[str]] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise AppException(ErrorRegistry.MINST_NAME_EMPTY)
        return v


__all__ = [
    "MinistereBase",
    "MinistereCreate",
    "MinistereRead",
    "MinistereReadWithRelations",
    "MinistereUpdate",
]
