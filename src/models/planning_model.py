import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel

from mla_enum.custom_enum import PlanningStatusCode

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
    activite_id: Optional[str] = Field(
        default=None, foreign_key="t_activite.id", ondelete="CASCADE", index=True
    )

    @field_validator("activite_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        # 2. Ajoute cette protection immédiate
        if v is None or v == "":
            return None

        try:
            # On s'assure que v est bien une string avant le check UUID
            uuid.UUID(str(v))
            return str(v)
        except (ValueError, TypeError) as e:
            raise ValueError("activite_id doit être un UUID valide") from e


class PlanningServiceUpdate(SQLModel):
    # Permet de mettre à jour uniquement le statut
    statut_code: Optional[str] = None


class PlanningServiceCreate(PlanningServiceBase):
    statut_code: str = PlanningStatusCode.BROUILLON.value
    activite_id: Optional[str] = Field(default=None, foreign_key="t_activite.id")

    @field_validator("activite_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        # 2. On ajoute cette condition : si v est None,
        #  on ne valide rien, on renvoie None.
        if v is None:
            return v
        try:
            uuid.UUID(str(v))
            return str(v)
        except (ValueError, TypeError) as e:
            raise ValueError("activite_id doit être un UUID valide") from e

    # On peut ajouter ici des champs spécifiques à la création si nécessaire
    # Exemple : des slots imbriqués (nested create)


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
    date_debut: datetime
    date_fin: datetime
    affectations: List[AffectationFullUpdate] = []


class PlanningFullUpdate(BaseModel):
    activite: Optional[ActiviteUpdate] = None
    # statut_code: Optional[str] = None
    planning: Optional[PlanningServiceUpdate] = None
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
