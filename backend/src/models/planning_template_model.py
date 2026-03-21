"""Schémas Pydantic pour les templates de planning."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PlanningTemplateRoleRead(BaseModel):
    """DTO lecture d'un rôle de créneau de template."""

    id: str
    role_code: str


class PlanningTemplateSlotRead(BaseModel):
    """DTO lecture d'un créneau de template."""

    id: str
    nom_creneau: str
    offset_debut_minutes: int
    offset_fin_minutes: int
    nb_personnes_requis: int
    roles: List[PlanningTemplateRoleRead]


class PlanningTemplateRead(BaseModel):
    """DTO lecture complet d'un template de planning."""

    id: str
    nom: str
    description: Optional[str]
    activite_type: str
    duree_minutes: int
    campus_id: str
    ministere_id: str
    created_by_id: str
    created_at: datetime
    used_count: int
    slots: List[PlanningTemplateSlotRead]


class SaveAsTemplateRequest(BaseModel):
    """Payload pour sauvegarder un planning comme template."""

    nom: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("nom")
    @classmethod
    def nom_not_blank(cls, v: str) -> str:
        """Vérifie que le nom n'est pas vide après strip."""
        if not v.strip():
            raise ValueError("Le nom du template ne peut pas être vide")
        return v.strip()


class PlanningTemplateUpdate(BaseModel):
    """Payload de mise à jour partielle d'un template."""

    nom: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
