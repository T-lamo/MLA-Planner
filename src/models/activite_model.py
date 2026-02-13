from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel


class ActiviteBase(SQLModel):
    type: str = Field(
        min_length=2,
        max_length=100,
        description="Type d'activité (ex: Cours, Conférence, Atelier)",
    )

    date_debut: datetime = Field(description="Date et heure de début de l'activité")

    date_fin: datetime = Field(description="Date et heure de fin de l'activité")

    lieu: Optional[str] = Field(
        default=None, min_length=2, max_length=255, description="Lieu de l'activité"
    )

    description: Optional[str] = Field(
        default=None, max_length=1000, description="Description détaillée de l'activité"
    )

    # campus_id: str = Field(min_length=36, max_length=36, description="UUID du campus")

    # ======================
    # VALIDATION CHAMPS
    # ======================

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if not v.strip():
            raise ValueError("Le type d'activité ne peut pas être vide")
        return v.title()

    # ======================
    # VALIDATION METIER
    # ======================
    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_fin <= self.date_debut:
            raise ValueError("date_fin doit être postérieure à date_debut")
        return self


class ActiviteCreate(ActiviteBase):
    """
    Tous les champs sont obligatoires à la création
    """


class ActiviteUpdate(SQLModel):
    type: Optional[str] = Field(None, min_length=2, max_length=100)
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    # campus_id: Optional[str] = Field(None, min_length=36, max_length=36)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin:
            if self.date_fin <= self.date_debut:
                raise ValueError("date_fin doit être postérieure à date_debut")
        return self


class ActiviteRead(ActiviteBase):
    id: str
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = ["ActiviteBase", "ActiviteRead", "ActiviteUpdate", "ActiviteCreate"]
