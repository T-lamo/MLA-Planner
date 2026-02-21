from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel

from core.exceptions.app_exception import AppException

# Importation du registre et de AppException
from core.message import ErrorRegistry


class ActiviteBase(SQLModel):
    type: str = Field(
        min_length=2,
        max_length=100,
        description="Type d'activité (ex: Cours, Conférence, Atelier)",
    )
    date_debut: datetime = Field(description="Date et heure de début de l'activité")
    date_fin: datetime = Field(description="Date et heure de fin de l'activité")
    lieu: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    campus_id: str = Field(description="ID du campus")
    ministere_organisateur_id: str = Field(description="ID du ministère organisateur")

    # ======================
    # VALIDATION CHAMPS
    # ======================

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if not v.strip():
            # Levée de l'AppException
            raise AppException(ErrorRegistry.ACTV_TYPE_EMPTY)
        return v.title()

    # ======================
    # VALIDATION METIER
    # ======================
    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_fin <= self.date_debut:
            # Levée de l'AppException
            raise AppException(ErrorRegistry.ACTV_INVALID_CHRONOLOGY)
        return self


class ActiviteCreate(ActiviteBase):
    """Tous les champs sont obligatoires à la création"""


class ActiviteUpdate(SQLModel):
    type: Optional[str] = Field(None, min_length=2, max_length=100)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin:
            if self.date_fin <= self.date_debut:
                # Levée de l'AppException
                raise AppException(ErrorRegistry.ACTV_INVALID_CHRONOLOGY)
        return self


class ActiviteRead(ActiviteBase):
    id: str
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = ["ActiviteBase", "ActiviteRead", "ActiviteUpdate", "ActiviteCreate"]
