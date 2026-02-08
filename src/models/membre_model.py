from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from models.utilisateur_model import UtilisateurRead


# -------------------------
# BASE
# -------------------------
class MembreBase(SQLModel):
    nom: str = Field(index=True, max_length=50)
    prenom: str = Field(max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100, unique=True)
    telephone: Optional[str] = Field(
        default=None, max_length=20, schema_extra={"pattern": r"^\+?[0-9\s\-]+$"}
    )
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
    ministere_id: Optional[UUID] = None
    pole_id: Optional[UUID] = None


class MembreRead(MembreBase):
    id: str
    date_inscription: datetime  # Type strict datetime
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None
    utilisateur: Optional[UtilisateurRead] = None
    model_config = {"from_attributes": True}


class MembrePaginatedResponse(SQLModel):
    total: int
    limit: int
    offset: int
    data: List[MembreRead]
    model_config = {"from_attributes": True}


class MembreUpdate(SQLModel):
    nom: Optional[str] = Field(default=None, max_length=50)
    prenom: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: Optional[bool] = None
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
