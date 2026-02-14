import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from models.affectation_model import AffectationBase
from models.equipe_model import EquipeBase
from models.planning_model import PlanningServiceBase
from models.slot_model import SlotBase

from .activite_model import ActiviteBase
from .affectation_context_model import AffectationContexteBase
from .affectation_role_model import AffectationRoleBase
from .campus_model import CampusBase
from .categorie_role_model import CategorieRoleBase
from .indisponibilite_model import IndisponibiliteBase
from .membre_model import MembreBase
from .membre_role_model import MembreRoleBase
from .ministere_model import MinistereBase
from .organisationicc_model import OrganisationICCBase
from .pays_model import PaysBase
from .permission_model import PermissionBase
from .pole_model import PoleBase
from .role_competence_model import RoleCompetenceBase
from .role_model import RoleBase
from .utilisateur_model import UtilisateurBase

# -------------------------
# 1. RÉFÉRENTIELS & POLYVALENCE
# -------------------------


class CategorieRole(CategorieRoleBase, table=True):  # type: ignore
    __tablename__ = "t_categorierole"
    roles: List["RoleCompetence"] = Relationship(back_populates="categorie")


class RoleCompetence(RoleCompetenceBase, table=True):  # type: ignore
    __tablename__ = "t_rolecompetence"
    categorie: Optional[CategorieRole] = Relationship(back_populates="roles")
    membres_assoc: List["MembreRole"] = Relationship(back_populates="role")


class MembreRole(MembreRoleBase, table=True):  # type: ignore
    __tablename__ = "t_membre_role"
    membre: "Membre" = Relationship(back_populates="roles_assoc")
    role: "RoleCompetence" = Relationship(back_populates="membres_assoc")


class StatutPlanning(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_statutplanning"
    code: str = Field(primary_key=True, max_length=20)
    plannings: List["PlanningService"] = Relationship(back_populates="statut")


class TypeResponsabilite(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_typeresponsabilite"
    code: str = Field(primary_key=True, max_length=50)
    responsabilites: List["Responsabilite"] = Relationship(
        back_populates="type_responsabilite"
    )


# -------------------------
# 2. STRUCTURE ORGANISATIONNELLE
# -------------------------


class OrganisationICC(OrganisationICCBase, table=True):  # type: ignore
    __tablename__ = "t_organisationicc"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    date_creation: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pays: List["Pays"] = Relationship(back_populates="organisation")


class Pays(PaysBase, table=True):  # type: ignore
    __tablename__ = "t_pays"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    organisation_id: Optional[str] = Field(
        default=None, foreign_key="t_organisationicc.id", ondelete="SET NULL"
    )
    organisation: Optional["OrganisationICC"] = Relationship(back_populates="pays")
    campus: List["Campus"] = Relationship(back_populates="pays")


class Campus(CampusBase, table=True):  # type: ignore
    __tablename__ = "t_campus"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    pays_id: str = Field(foreign_key="t_pays.id", ondelete="CASCADE")
    pays: Optional["Pays"] = Relationship(back_populates="campus")
    ministeres: List["Ministere"] = Relationship(back_populates="campus")
    activites: List["Activite"] = Relationship(back_populates="campus")
    membres: List["Membre"] = Relationship(back_populates="campus")


class Ministere(MinistereBase, table=True):  # type: ignore
    __tablename__ = "t_ministere"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    campus_id: str = Field(foreign_key="t_campus.id", ondelete="CASCADE")
    campus: Optional["Campus"] = Relationship(back_populates="ministeres")
    poles: List["Pole"] = Relationship(back_populates="ministere")
    membres: List["Membre"] = Relationship(back_populates="ministere")
    equipes: List["Equipe"] = Relationship(back_populates="ministere")


class Pole(PoleBase, table=True):  # type: ignore
    __tablename__ = "t_pole"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    ministere_id: str = Field(foreign_key="t_ministere.id", ondelete="CASCADE")
    ministere: Optional["Ministere"] = Relationship(back_populates="poles")
    membres: List["Membre"] = Relationship(back_populates="pole")


# -------------------------
# 3. MEMBRES & RH
# -------------------------


class Membre(MembreBase, table=True):  # type: ignore
    __tablename__ = "t_membre"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date_inscription: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    campus_id: str = Field(foreign_key="t_campus.id", ondelete="CASCADE", index=True)
    ministere_id: Optional[str] = Field(
        default=None, foreign_key="t_ministere.id", ondelete="SET NULL", index=True
    )
    pole_id: Optional[str] = Field(
        default=None, foreign_key="t_pole.id", ondelete="SET NULL", index=True
    )

    campus: Optional["Campus"] = Relationship(back_populates="membres")
    ministere: Optional["Ministere"] = Relationship(back_populates="membres")
    pole: Optional["Pole"] = Relationship(back_populates="membres")
    roles_assoc: List["MembreRole"] = Relationship(back_populates="membre")
    affectations: List["Affectation"] = Relationship(back_populates="membre")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="membre")
    equipes_assoc: List["EquipeMembre"] = Relationship(back_populates="membre")
    indisponibilites: List["Indisponibilite"] = Relationship(back_populates="membre")
    utilisateur: Optional["Utilisateur"] = Relationship(
        back_populates="membre", sa_relationship_kwargs={"uselist": False}
    )


# -------------------------
# 4. OPÉRATIONNEL & PLANNING
# -------------------------


class Activite(ActiviteBase, table=True):  # type: ignore
    __tablename__ = "t_activite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    campus_id: str = Field(foreign_key="t_campus.id", ondelete="CASCADE")
    campus: Optional["Campus"] = Relationship(back_populates="activites")
    planning_services: List["PlanningService"] = Relationship(back_populates="activite")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="activite")
    ministere_organisateur_id: str = Field(
        foreign_key="t_ministere.id", ondelete="CASCADE"
    )


class Slot(SlotBase, table=True):  # type: ignore
    __tablename__ = "t_slot"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    planning: Optional["PlanningService"] = Relationship(back_populates="slots")
    affectations: List["Affectation"] = Relationship(back_populates="slot")


class PlanningService(PlanningServiceBase, table=True):  # type: ignore
    __tablename__ = "t_planningservice"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    deleted_at: Optional[datetime] = None
    activite: Optional["Activite"] = Relationship(back_populates="planning_services")
    statut: Optional[StatutPlanning] = Relationship(back_populates="plannings")
    slots: List["Slot"] = Relationship(
        back_populates="planning",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StatutAffectation(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_statutaffectation"
    code: str = Field(primary_key=True, max_length=20)
    libelle: Optional[str] = None
    affectations: List["Affectation"] = Relationship(back_populates="statut_aff")


class Affectation(AffectationBase, table=True):  # type: ignore
    __tablename__ = "t_affectation"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    slot: Optional[Slot] = Relationship(back_populates="affectations")
    statut_aff: Optional[StatutAffectation] = Relationship(
        back_populates="affectations"
    )
    membre: Optional["Membre"] = Relationship(back_populates="affectations")

    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ["membre_id", "role_code"],
    #         ["t_membre_role.membre_id", "t_membre_role.role_code"],
    #         ondelete="CASCADE",
    #     ),
    # )


# -------------------------
# 5. GOUVERNANCE & SÉCURITÉ
# -------------------------


class Responsabilite(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_responsabilite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    actif: bool = Field(default=True)
    type_code: str = Field(foreign_key="t_typeresponsabilite.code", ondelete="CASCADE")
    membre_id: str = Field(foreign_key="t_membre.id", ondelete="CASCADE")
    ministere_id: Optional[str] = Field(
        default=None, foreign_key="t_ministere.id", ondelete="CASCADE"
    )
    pole_id: Optional[str] = Field(
        default=None, foreign_key="t_pole.id", ondelete="CASCADE"
    )
    activite_id: Optional[str] = Field(
        default=None, foreign_key="t_activite.id", ondelete="CASCADE"
    )

    membre: Optional["Membre"] = Relationship(back_populates="responsabilites")
    type_responsabilite: Optional["TypeResponsabilite"] = Relationship(
        back_populates="responsabilites"
    )
    activite: Optional["Activite"] = Relationship(back_populates="responsabilites")


class Indisponibilite(IndisponibiliteBase, table=True):  # type: ignore
    __tablename__ = "t_indisponibilite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    membre_id: str = Field(foreign_key="t_membre.id", ondelete="CASCADE")
    membre: Optional["Membre"] = Relationship(back_populates="indisponibilites")


class Utilisateur(UtilisateurBase, table=True):  # type: ignore
    __tablename__ = "t_utilisateur"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    password: str = Field(max_length=255)
    membre_id: Optional[str] = Field(
        default=None, foreign_key="t_membre.id", unique=True
    )
    membre: Optional["Membre"] = Relationship(back_populates="utilisateur")
    affectations: List["AffectationRole"] = Relationship(back_populates="utilisateur")


class TokenBlacklist(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_revoked_tokens"
    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str = Field(index=True, unique=True)
    expires_at: datetime = Field(nullable=False)
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -------------------------
# 6. RBAC & ÉQUIPES
# -------------------------


class EquipeMembre(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_equipe_membre"
    equipe_id: str = Field(
        foreign_key="t_equipe.id", primary_key=True, ondelete="CASCADE"
    )
    membre_id: str = Field(
        foreign_key="t_membre.id", primary_key=True, ondelete="CASCADE"
    )
    equipe: Optional["Equipe"] = Relationship(back_populates="membres_assoc")
    membre: Optional["Membre"] = Relationship(back_populates="equipes_assoc")


# -------------------------
# 1. MODÈLE DB (Table)
# -------------------------
class Equipe(EquipeBase, table=True):  # type: ignore
    __tablename__ = "t_equipe"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    # Clé étrangère
    ministere_id: str = Field(foreign_key="t_ministere.id", ondelete="CASCADE")

    # Relations
    ministere: Optional["Ministere"] = Relationship(back_populates="equipes")
    membres_assoc: List["EquipeMembre"] = Relationship(back_populates="equipe")


class RolePermission(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_role_permission"
    role_id: str = Field(foreign_key="t_role.id", primary_key=True, ondelete="CASCADE")
    permission_id: str = Field(
        foreign_key="t_permission.id", primary_key=True, ondelete="CASCADE"
    )


class Role(RoleBase, table=True):  # type: ignore
    __tablename__ = "t_role"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    affectations: List["AffectationRole"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermission
    )


class Permission(PermissionBase, table=True):  # type: ignore
    __tablename__ = "t_permission"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    code: str = Field(index=True, unique=True, max_length=100)
    roles: List["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )


class AffectationRole(AffectationRoleBase, table=True):  # type: ignore
    __tablename__ = "t_affectation_role"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    utilisateur_id: str = Field(foreign_key="t_utilisateur.id", ondelete="CASCADE")
    role_id: str = Field(foreign_key="t_role.id", ondelete="CASCADE")
    utilisateur: Optional["Utilisateur"] = Relationship(back_populates="affectations")
    role: Optional["Role"] = Relationship(back_populates="affectations")
    contextes: List["AffectationContexte"] = Relationship(back_populates="affectation")


class AffectationContexte(AffectationContexteBase, table=True):  # type: ignore
    __tablename__ = "t_affectation_contexte"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    affectation_role_id: str = Field(
        foreign_key="t_affectation_role.id", ondelete="CASCADE"
    )
    ministere_id: Optional[str] = Field(
        default=None, foreign_key="t_ministere.id", ondelete="CASCADE"
    )
    pole_id: Optional[str] = Field(
        default=None, foreign_key="t_pole.id", ondelete="CASCADE"
    )
    activite_id: Optional[str] = Field(
        default=None, foreign_key="t_activite.id", ondelete="CASCADE"
    )
    affectation: Optional["AffectationRole"] = Relationship(back_populates="contextes")


__all__ = [
    "CategorieRole",
    "RoleCompetence",
    "Slot",
    "StatutAffectation",
    "MembreRole",
    "StatutPlanning",
    "TypeResponsabilite",
    "OrganisationICC",
    "Pays",
    "Campus",
    "Ministere",
    "Pole",
    "Membre",
    "Indisponibilite",
    "Activite",
    "PlanningService",
    "Affectation",
    "Responsabilite",
    "Utilisateur",
    "TokenBlacklist",
    "Equipe",
    "EquipeMembre",
    "Role",
    "Permission",
    "RolePermission",
    "AffectationRole",
    "AffectationContexte",
]
