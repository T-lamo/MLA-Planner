from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, field_validator
from sqlmodel import Field, SQLModel

from models.membre_role_model import MembreRoleRead
from models.utilisateur_model import UtilisateurRead


# -------------------------
# BASE
# -------------------------
class MembreBase(SQLModel):
    nom: str = Field(index=True, max_length=50)
    prenom: str = Field(max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: bool = Field(default=True)

    @field_validator("nom", "prenom")
    @classmethod
    def capitalize_names(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip().title()

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


# -------------------------
# SCHÉMAS (DTO)
# -------------------------
class MembreCreate(MembreBase):
    campus_id: str  # Obligatoire d'après tes erreurs NotNullViolation
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None


class MembreRead(MembreBase):
    id: str
    date_inscription: datetime
    campus_id: str
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None
    utilisateur: Optional[UtilisateurRead] = None
    roles_assoc: List[MembreRoleRead] = []
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class MembrePaginatedResponse(SQLModel):
    total: int
    limit: int
    offset: int
    data: List[MembreRead]
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class MembreUpdate(SQLModel):
    nom: Optional[str] = Field(default=None, max_length=50)
    prenom: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: Optional[bool] = None
    campus_id: Optional[str] = None
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None


__all__ = [
    "MembreBase",
    "MembreCreate",
    "MembreRead",
    "MembreUpdate",
    "MembrePaginatedResponse",
]

MembreRead.model_rebuild()
