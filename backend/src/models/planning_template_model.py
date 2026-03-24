"""Schémas Pydantic pour les templates de planning."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


class PlanningTemplateRoleMembreRead(BaseModel):
    """DTO lecture d'un membre suggéré pour un rôle de template."""

    id: str
    membre_id: str
    membre_nom: str
    membre_username: str


class PlanningTemplateRoleRead(BaseModel):
    """DTO lecture d'un rôle de créneau de template."""

    id: str
    role_code: str
    membres_suggeres: List[PlanningTemplateRoleMembreRead] = Field(default_factory=list)


class PlanningTemplateRoleWrite(BaseModel):
    """Payload création/remplacement d'un rôle de template."""

    role_code: str
    membres_suggeres_ids: List[str] = Field(default_factory=list)


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


# Alias pour cohérence avec la convention US-95
PlanningTemplateReadFull = PlanningTemplateRead


class PlanningTemplateListItem(BaseModel):
    """DTO liste des templates — vue résumée."""

    id: str
    nom: str
    description: Optional[str] = None
    ministere_id: str
    campus_id: str
    activite_type: Optional[str] = None
    nb_creneaux: int
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime


class PlanningTemplateSlotWrite(BaseModel):
    """Payload création/remplacement d'un créneau de template."""

    nom_creneau: str = Field(min_length=1, max_length=100)
    offset_debut_minutes: int = Field(ge=0)
    offset_fin_minutes: int = Field(ge=1)
    nb_personnes_requis: int = Field(default=1, ge=1)
    roles: List[PlanningTemplateRoleWrite]


class PlanningTemplateFullUpdate(BaseModel):
    """Payload de mise à jour complète d'un template (slots inclus)."""

    nom: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    slots: List[PlanningTemplateSlotWrite]


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
    """Payload de mise à jour partielle d'un template (nom/desc seulement)."""

    nom: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)


# ── TypedDict résultats apply US-96 ───────────────────────────────────────────


class WarningIndispo(TypedDict):
    """Avertissement : membre indisponible à la date du planning."""

    membre_id: str
    membre_nom: str
    creneau_nom: str
    role_code: str


class WarningMembreIgnore(TypedDict):
    """Avertissement : membre ignoré lors de l'application."""

    membre_id: str
    membre_nom: str
    role_code: str
    raison: str  # "hors_ministere" | "introuvable"


class ApplyTemplateResult(TypedDict):
    """Résultat de l'application d'un template sur un planning."""

    planning_id: str
    affectations_creees: int
    avertissements_indispo: List[WarningIndispo]
    membres_ignores: List[WarningMembreIgnore]


# ── Schéma Pydantic pour le response_model FastAPI ────────────────────────────


class ApplyTemplateResultSchema(BaseModel):
    """Schéma Pydantic miroir de ApplyTemplateResult (pour response_model)."""

    planning_id: str
    affectations_creees: int
    avertissements_indispo: List[WarningIndispo]
    membres_ignores: List[WarningMembreIgnore]
