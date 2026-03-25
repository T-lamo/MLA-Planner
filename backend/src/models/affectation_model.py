from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator
from sqlmodel import Field, SQLModel


class AffectationBase(SQLModel):
    slot_id: str = Field(foreign_key="t_slot.id", ondelete="CASCADE")
    membre_id: str = Field(foreign_key="t_membre.id", ondelete="CASCADE")
    role_code: str = Field(max_length=50)
    statut_affectation_code: str = Field(foreign_key="t_statutaffectation.code")
    presence_confirmee: bool = Field(default=False)
    ministere_id: Optional[str] = Field(
        default=None, foreign_key="t_ministere.id", ondelete="SET NULL"
    )


class AffectationUpdate(SQLModel):
    role_code: Optional[str] = Field(default=None, max_length=50)
    statut_affectation_code: Optional[str] = Field(default=None)
    presence_confirmee: Optional[bool] = None


class AffectationCreate(AffectationBase):
    pass


class AffectationRead(AffectationBase):
    id: str


class AffectationMemberRead(BaseModel):
    """Vue enrichie d'une affectation pour un membre (page mes-affectations)."""

    id: str
    statut_affectation_code: str
    role_code: str
    slot_nom: str
    slot_debut: datetime
    slot_fin: datetime
    activite_type: Optional[str] = None
    ministere_nom: Optional[str] = None
    lieu: Optional[str] = None
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def flatten_relations(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        slot = getattr(data, "slot", None)
        planning = getattr(slot, "planning", None) if slot else None
        activite = getattr(planning, "activite", None) if planning else None
        ministere = getattr(data, "ministere", None)
        return {
            "id": getattr(data, "id", None),
            "statut_affectation_code": getattr(data, "statut_affectation_code", None),
            "role_code": getattr(data, "role_code", None),
            "slot_nom": getattr(slot, "nom_creneau", "") if slot else "",
            "slot_debut": getattr(slot, "date_debut", None) if slot else None,
            "slot_fin": getattr(slot, "date_fin", None) if slot else None,
            "activite_type": getattr(activite, "type", None) if activite else None,
            "ministere_nom": getattr(ministere, "nom", None) if ministere else None,
            "lieu": getattr(activite, "lieu", None) if activite else None,
        }


__all__ = [
    "AffectationBase",
    "AffectationCreate",
    "AffectationMemberRead",
    "AffectationRead",
    "AffectationUpdate",
]
