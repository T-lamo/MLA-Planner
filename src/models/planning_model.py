import uuid
from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from models.slot_model import SlotRead

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


# Pour éviter les problèmes de circularité avec SlotRead
PlanningServiceRead.model_rebuild()

__all__ = [
    "PlanningServiceBase",
    "PlanningServiceCreate",
    "PlanningServiceRead",
    "PlanningServiceUpdate",  # Correction orthographe
]
