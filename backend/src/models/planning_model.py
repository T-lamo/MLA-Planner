import uuid
from datetime import datetime
from typing import List, Optional

from mla_enum.custom_enum import PlanningStatusCode
from pydantic import BaseModel, computed_field, field_validator
from sqlmodel import Field, SQLModel

from .activite_model import ActiviteCreate, ActiviteRead, ActiviteUpdate
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


class AffectationSimpleCreate(BaseModel):
    membre_id: str
    role_code: str


class SlotWithAffectationsCreate(SlotCreate):
    # On surcharge pour inclure les affectations dans le payload
    affectations: List[AffectationSimpleCreate]


class SlotFullNested(
    BaseModel
):  # On n'hérite plus de SlotCreate pour éviter les IDs obligatoires
    nom_creneau: str
    date_debut: datetime
    date_fin: datetime
    # On omet volontairement planning_id ici
    affectations: List[AffectationSimpleCreate]


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


class MemberSummaryRead(BaseModel):
    id: str
    nom: str
    prenom: str
    model_config = {"from_attributes": True}


class AffectationFullRead(BaseModel):
    id: str
    statut_affectation_code: str
    role_code: str
    membre: Optional[MemberSummaryRead] = None
    model_config = {"from_attributes": True}


class SlotFullRead(BaseModel):
    id: str
    nom_creneau: str
    date_debut: datetime
    date_fin: datetime
    nb_personnes_requis: int
    affectations: List[AffectationFullRead] = []
    model_config = {"from_attributes": True}

    @computed_field
    def filling_rate(self) -> float:
        if self.nb_personnes_requis <= 0:
            return 0.0
        rate = (len(self.affectations) / self.nb_personnes_requis) * 100
        return round(min(rate, 100.0), 2)


class ViewContext(BaseModel):
    allowed_transitions: List[str]
    total_slots: int
    filled_slots: int
    is_ready_for_publish: bool


class PlanningFullRead(PlanningServiceBase):
    id: str
    activite: Optional[ActiviteRead] = None
    slots: List[SlotFullRead] = []
    view_context: Optional[ViewContext] = None
    model_config = {"from_attributes": True}


# Pour éviter les problèmes de circularité avec SlotRead
PlanningServiceRead.model_rebuild()

__all__ = [
    # Base et CRUD standard
    "PlanningServiceBase",
    "PlanningServiceCreate",
    "PlanningServiceRead",
    "PlanningServiceUpdate",
    # Création (Full/Nested)
    "PlanningFullCreate",
    "SlotFullNested",
    "SlotWithAffectationsCreate",
    "AffectationSimpleCreate",
    # Mise à jour (Full/Nested)
    "PlanningFullUpdate",
    "SlotFullUpdate",
    "AffectationFullUpdate",
    # Lecture (Full/DTOs)
    "PlanningFullRead",
    "SlotFullRead",
    "AffectationFullRead",
    "MemberSummaryRead",
    "ViewContext",
]
