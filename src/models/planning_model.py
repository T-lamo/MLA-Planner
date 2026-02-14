import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel

from .activite_model import ActiviteCreate, ActiviteUpdate
from .slot_model import SlotCreate, SlotRead

# Import de l'enum défini plus haut
# from mla_enum import PlanningStatusCode


class PlanningServiceBase(SQLModel):
    # Utilisation de l'Enum pour le typage Python et validation automatique
    statut_code: str = Field(
        foreign_key="t_statutplanning.code",
        ondelete="CASCADE",
        default="BROUILLON",
        index=True,
    )
    activite_id: str = Field(
        foreign_key="t_activite.id", ondelete="CASCADE", index=True
    )

    @field_validator("activite_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Vérifie que l'ID de l'activité est un UUID valide."""
        try:
            uuid.UUID(v)
            return v
        except ValueError as e:
            raise ValueError("activite_id doit être un UUID valide") from e


class PlanningServiceUpdate(SQLModel):
    # Permet de mettre à jour uniquement le statut
    statut_code: Optional[str] = None


class PlanningServiceCreate(PlanningServiceBase):
    # On peut ajouter ici des champs spécifiques à la création si nécessaire
    # Exemple : des slots imbriqués (nested create)
    pass


class PlanningServiceRead(PlanningServiceBase):
    id: str
    # Les slots sont souvent chargés de manière asynchrone ou via selectinload
    slots: List["SlotRead"] = []


class AssignmentSimpleCreate(BaseModel):
    membre_id: str
    role_code: str


class SlotWithAssignmentsCreate(SlotCreate):
    # On surcharge pour inclure les affectations dans le payload
    affectations: List[AssignmentSimpleCreate]


class SlotFullNested(
    BaseModel
):  # On n'hérite plus de SlotCreate pour éviter les IDs obligatoires
    nom_creneau: str
    date_debut: datetime
    date_fin: datetime
    # On omet volontairement planning_id ici
    affectations: List[AssignmentSimpleCreate]


class PlanningFullCreate(BaseModel):
    activite: ActiviteCreate
    planning: Optional[PlanningServiceCreate] = None
    slots: List[SlotFullNested]


class AffectationFullUpdate(BaseModel):
    id: Optional[str] = None  # Si présent : update, si absent : create
    membre_id: str
    role_code: str
    statut_affectation_code: Optional[str] = None


class SlotFullUpdate(BaseModel):
    id: Optional[str] = None
    nom_creneau: str
    date_debut: str
    date_fin: str
    affectations: List[AffectationFullUpdate] = []


class PlanningFullUpdate(BaseModel):
    activite: Optional[ActiviteUpdate] = None
    statut_code: Optional[str] = None
    slots: List[SlotFullUpdate] = []


# Pour éviter les problèmes de circularité avec SlotRead
PlanningServiceRead.model_rebuild()

__all__ = [
    "PlanningServiceBase",
    "PlanningServiceCreate",
    "PlanningServiceRead",
    "PlanningServiceUpdate",
    "PlanningFullCreate",
    "SlotFullNested",
    # Correction orthographe
]
