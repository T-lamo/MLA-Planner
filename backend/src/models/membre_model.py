from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlmodel import Field, SQLModel

from .categorie_role_model import RoleWithCategoryRead
from .membre_role_model import MembreRoleRead
from .utilisateur_model import UtilisateurRead

# --- VERSIONS "SIMPLE" POUR LE CONTEXTE MEMBRE ---


class UtilisateurSimple(UtilisateurRead):
    """Vue utilisateur sans membre_id (le parent est déjà le membre)."""

    membre_id: Optional[str] = None  # type: ignore[assignment]


class MembreRoleSimple(MembreRoleRead):
    """Vue rôle sans membre_id."""

    membre_id: Optional[str] = None  # type: ignore[assignment]


class MembreRoleRich(MembreRoleSimple):
    """
    Version de l'association qui accepte et valide l'objet 'role'
    injecté par selectinload.
    """

    role: Optional[RoleWithCategoryRead] = None


# -------------------------
# BASE
# -------------------------
class MembreBase(SQLModel):
    nom: str = Field(index=True, max_length=50)
    prenom: str = Field(max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: bool = Field(default=True)
    campus_principal_id: Optional[str] = None

    @field_validator("nom", "prenom")
    @classmethod
    def capitalize_names(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip().title()

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


# -------------------------
# NEW: MEMBRE SIMPLE
# -------------------------
class MembreSimple(MembreBase):
    """
    Version ultra-légère du membre.
    Utilisée pour les listes de membres dans le détail des Ministères ou Pôles.
    Exclut l'utilisateur et les rôles pour la performance.
    """

    id: str
    date_inscription: datetime
    model_config = {"from_attributes": True}


class MembreSimpleWithRoles(MembreSimple):
    """MembreSimple enrichi des role_codes de compétence."""

    roles: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# -------------------------
# READ (Version Allégée - Utilisée partout en imbriqué)
# -------------------------
class MembreRead(MembreBase):
    """
    Version de base pour la lecture.
    Contient l'utilisateur et les rôles en version 'Simple'.
    Exclut les listes complexes (campuses, ministeres, poles).
    """

    id: str
    date_inscription: datetime
    utilisateur: Optional[UtilisateurSimple] = None
    roles_assoc: Sequence[MembreRoleSimple] = []

    model_config = {"from_attributes": True}


# -------------------------
# CREATE / UPDATE (Identiques mais avec validations)
# -------------------------
class MembreCreate(MembreBase):
    campus_ids: List[str] = Field(default=[], description="Liste des UUIDs")
    ministere_ids: List[str] = Field(default=[], description="Liste des UUIDs")
    pole_ids: List[str] = Field(default=[], description="Liste des UUIDs")


class MembreUpdate(SQLModel):
    nom: Optional[str] = Field(default=None, max_length=50)
    prenom: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    telephone: Optional[str] = Field(default=None, max_length=20)
    actif: Optional[bool] = None
    campus_ids: Optional[List[str]] = None
    ministere_ids: Optional[List[str]] = None
    pole_ids: Optional[List[str]] = None
    campus_principal_id: Optional[str] = None


# -------------------------
# RÉPONSES PAGINÉES
# -------------------------
class MembrePaginatedResponse(SQLModel):
    total: int
    limit: int
    offset: int
    data: List[MembreRead]
    model_config = {"from_attributes": True}


# --- SCHÉMAS D'AGENDA (Inchangés mais conservés pour export) ---


class MemberAgendaEntryRead(BaseModel):
    affectation_id: str
    statut_affectation_code: str
    role_code: str
    nom_creneau: str
    date_debut: datetime
    date_fin: datetime
    activite_nom: str
    activite_type: str
    lieu: Optional[str] = None
    campus_nom: str
    model_config = ConfigDict(from_attributes=True)


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
    "UtilisateurSimple",
    "MembreRoleSimple",
    "MembreSimple",
    "MembreSimpleWithRoles",
    "MembreRoleRich",
]
