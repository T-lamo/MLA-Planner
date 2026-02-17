from typing import List, Optional

from pydantic import ConfigDict, computed_field, field_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Importation du registre et de l'AppException
from core.message import ErrorRegistry

from .membre_model import MembreRead
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
            # Utilisation de AppException au lieu de ValueError
            raise AppException(ErrorRegistry.MINST_NAME_EMPTY)
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

    # On rend ces champs optionnels pour éviter les ResponseValidationError
    # si les relations ne sont pas "eager loaded"
    poles: List[PoleRead] = []
    membres: List[MembreRead] = []

    model_config = ConfigDict(from_attributes=True)  # type: ignore

    @computed_field
    def poles_count(self) -> int:
        return len(self.poles) if self.poles else 0

    @computed_field
    def membres_count(self) -> int:
        return len(self.membres) if self.membres else 0


# -------------------------
# UPDATE
# -------------------------
class MinistereUpdate(SQLModel):
    nom: Optional[str] = None
    date_creation: Optional[str] = None
    actif: Optional[bool] = None
    campus_id: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            # Utilisation de AppException au lieu de ValueError
            raise AppException(ErrorRegistry.MINST_NAME_EMPTY)
        return v


__all__ = [
    "MinistereBase",
    "MinistereCreate",
    "MinistereRead",
    "MinistereUpdate",
]
