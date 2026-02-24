from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlmodel import Field, SQLModel

from models.campus_model import CampusRead
from models.membre_role_model import MembreRoleRead

if TYPE_CHECKING:
    from models.ministere_model import MinistereRead
    from models.pole_model import PoleRead
    from models.utilisateur_model import UtilisateurRead


# -------------------------
# BASE
# -------------------------
class MembreBase(SQLModel):
    nom: str = Field(index=True, max_length=50)
    prenom: str = Field(max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
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
    campus_ids: List[str] = Field(default=[], description="Liste des UUIDs des campus")
    ministere_ids: List[str] = Field(
        default=[], description="Liste des UUIDs des ministères"
    )
    pole_ids: List[str] = Field(default=[], description="Liste des UUIDs des pôles")


class MembreRead(MembreBase):
    id: str
    date_inscription: datetime
    campuses: List[CampusRead] = []
    ministeres: List["MinistereRead"] = []
    poles: List["PoleRead"] = []
    utilisateur: Optional["UtilisateurRead"] = None
    roles_assoc: List[MembreRoleRead] = []
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class MembrePaginatedResponse(SQLModel):
    total: int
    limit: int
    offset: int
    data: List[MembreRead]
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class MembreUpdate(SQLModel):
    nom: Optional[str] = Field(default=None, max_length=50)
    prenom: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: Optional[bool] = None
    campus_ids: Optional[List[str]] = None
    ministere_ids: Optional[List[str]] = None
    pole_ids: Optional[List[str]] = None


class MemberAgendaEntryRead(BaseModel):
    affectation_id: str
    statut_affectation_code: str
    role_code: str
    # Infos du créneau (venant du Slot)
    nom_creneau: str
    date_debut: datetime
    date_fin: datetime
    # Infos de l'activité (venant du Planning/Activite)
    activite_nom: str
    activite_type: str
    lieu: Optional[str] = None
    campus_nom: str

    model_config = {"from_attributes": True}


class MemberAgendaStats(BaseModel):
    total_engagements: int
    confirmed_rate: float
    roles_distribution: Dict[str, int]


class MemberAgendaResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    statistics: MemberAgendaStats
    entries: List[MemberAgendaEntryRead]


__all__ = [
    "MembreBase",
    "MembreCreate",
    "MembreRead",
    "MembreUpdate",
    "MembrePaginatedResponse",
    "MemberAgendaEntryRead",
    "MemberAgendaStats",
    "MemberAgendaResponse",
]
