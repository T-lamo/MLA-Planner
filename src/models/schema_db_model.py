# models.py
import uuid
from typing import List, Optional

from sqlalchemy import Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

from mla_enum import VoixEnum

from .activite_model import ActiviteBase
from .affectation_context_model import AffectationContexteBase
from .affectation_role_model import AffectationRoleBase
from .campus_model import CampusBase
from .chantre_model import ChantreBase
from .indisponibilite_model import IndisponibiliteBase
from .membre_model import MembreBase
from .ministere_model import MinistereBase
from .organisationicc_model import OrganisationICCBase
from .pays_model import PaysBase
from .permission_model import PermissionBase
from .pole_model import PoleBase
from .role_model import RoleBase
from .utilisateur_model import UtilisateurBase
from .voix_model import VoixBase


# -------------------------
# Tables de référence
# -------------------------
class Voix(VoixBase, table=True):  # type: ignore
    __tablename__ = "t_voix"

    code: VoixEnum = Field(primary_key=True)

    choristes: List["Choriste"] = Relationship(back_populates="voix")
    affectations: List["Affectation"] = Relationship(back_populates="voix")


class Instrument(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_instrument"

    code: str = Field(primary_key=True, max_length=20)

    musiciens: List["Musicien"] = Relationship(back_populates="instrument")
    affectations: List["Affectation"] = Relationship(back_populates="instrument")


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
# TABLE MODEL
# -------------------------
class OrganisationICC(OrganisationICCBase, table=True):  # type: ignore
    __tablename__ = "t_organisationicc"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    # Relations
    # On utilise back_populates pour l'intégrité avec la classe Pays
    pays: List["Pays"] = Relationship(back_populates="organisation")


# -------------------------
# TABLE MODEL
# -------------------------
class Pays(PaysBase, table=True):  # type: ignore
    __tablename__ = "t_pays"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    organisation_id: str = Field(
        foreign_key="t_organisationicc.id", nullable=False, ondelete="CASCADE"
    )

    # Relations
    organisation: Optional["OrganisationICC"] = Relationship(back_populates="pays")
    campus: List["Campus"] = Relationship(back_populates="pays")


# -------------------------
# TABLE MODEL
# -------------------------
class Campus(CampusBase, table=True):  # type: ignore
    __tablename__ = "t_campus"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    pays_id: str = Field(
        sa_column=Column(ForeignKey("t_pays.id", ondelete="CASCADE"), nullable=False)
    )

    # Relations
    pays: Optional["Pays"] = Relationship(back_populates="campus")
    ministeres: List["Ministere"] = Relationship(back_populates="campus")
    activites: List["Activite"] = Relationship(back_populates="campus")


# -------------------------
# Ministères & pôles
# -------------------------
class Ministere(MinistereBase, table=True):  # type: ignore
    __tablename__ = "t_ministere"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    campus_id: str = Field(
        sa_column=Column(ForeignKey("t_campus.id", ondelete="CASCADE"), nullable=False)
    )

    campus: Optional["Campus"] = Relationship(back_populates="ministeres")
    poles: List["Pole"] = Relationship(back_populates="ministere")
    membres: List["Membre"] = Relationship(back_populates="ministere")
    equipes: List["Equipe"] = Relationship(back_populates="ministere")


class Pole(PoleBase, table=True):  # type: ignore
    __tablename__ = "t_pole"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    ministere_id: str = Field(
        sa_column=Column(
            ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False
        )
    )

    ministere: Optional["Ministere"] = Relationship(back_populates="poles")
    membres: List["Membre"] = Relationship(back_populates="pole")


# -------------------------
# Membres
# -------------------------
class Membre(MembreBase, table=True):  # type: ignore
    __tablename__ = "t_membre"
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    dateInscription: Optional[str] = None
    ministere_id: str = Field(
        sa_column=Column(
            ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False
        )
    )

    pole_id: str = Field(
        sa_column=Column(ForeignKey("t_pole.id", ondelete="CASCADE"), nullable=False)
    )

    ministere: Optional[Ministere] = Relationship(back_populates="membres")
    pole: Optional[Pole] = Relationship(back_populates="membres")

    chantres: List["Chantre"] = Relationship(back_populates="membre")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="membre")
    equipes_assoc: List["Equipe_Membre"] = Relationship(back_populates="membre")
    utilisateur: Optional["Utilisateur"] = Relationship(
        back_populates="membre", sa_relationship_kwargs={"uselist": False}
    )


# -------------------------
# Chantres / Choristes / Musiciens
# -------------------------
class Chantre(ChantreBase, table=True):  # type: ignore
    __tablename__ = "t_chantre"
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    membre_id: str = Field(
        sa_column=Column(ForeignKey("t_membre.id", ondelete="CASCADE"), nullable=False)
    )

    membre: Optional[Membre] = Relationship(back_populates="chantres")
    choristes: List["Choriste"] = Relationship(back_populates="chantre")
    musiciens: List["Musicien"] = Relationship(back_populates="chantre")
    affectations: List["Affectation"] = Relationship(back_populates="chantre")
    indisponibilites: List["Indisponibilite"] = Relationship(back_populates="chantre")


class Choriste(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_choriste"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    voix_code: str = Field(
        sa_column=Column(ForeignKey("t_voix.code", ondelete="CASCADE"), nullable=False)
    )

    secondaireVoix: Optional[str] = None

    chantre_id: str = Field(
        sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False)
    )

    chantre: Optional[Chantre] = Relationship(back_populates="choristes")
    voix: Optional[Voix] = Relationship(back_populates="choristes")


class Musicien(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_musicien"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    instrument_code: str = Field(
        sa_column=Column(
            ForeignKey("t_instrument.code", ondelete="CASCADE"), nullable=False
        )
    )

    instrumentPrincipal: Optional[str] = None

    chantre_id: str = Field(
        sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False)
    )

    chantre: Optional[Chantre] = Relationship(back_populates="musiciens")
    instrument: Optional[Instrument] = Relationship(back_populates="musiciens")


# -------------------------
# Équipes
# -------------------------
class Equipe(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_equipe"
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    nom: str
    active: bool = True
    ministere_id: str = Field(
        sa_column=Column(
            ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False
        )
    )
    ministere: Optional[Ministere] = Relationship(back_populates="equipes")
    membres_assoc: List["Equipe_Membre"] = Relationship(back_populates="equipe")


class Equipe_Membre(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_equipe_membre"

    equipe_id: str = Field(
        sa_column=Column(
            ForeignKey("t_equipe.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )

    membre_id: str = Field(
        sa_column=Column(
            ForeignKey("t_membre.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )

    equipe: Optional[Equipe] = Relationship(back_populates="membres_assoc")
    membre: Optional[Membre] = Relationship(back_populates="equipes_assoc")


# -------------------------
# Activités & planning
# -------------------------
class Activite(ActiviteBase, table=True):  # type: ignore
    __tablename__ = "t_activite"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    campus_id: str = Field(
        sa_column=Column(ForeignKey("t_campus.id", ondelete="CASCADE"), nullable=False)
    )

    campus: Optional[Campus] = Relationship(back_populates="activites")
    planning_services: List["PlanningService"] = Relationship(back_populates="activite")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="activite")


class PlanningService(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_planningservice"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    dateCreation: Optional[str] = None

    statut_code: str = Field(
        sa_column=Column(
            ForeignKey("t_statutplanning.code", ondelete="CASCADE"), nullable=False
        )
    )

    activite_id: str = Field(
        sa_column=Column(
            ForeignKey("t_activite.id", ondelete="CASCADE"), nullable=False
        )
    )
    activite: Optional[Activite] = Relationship(back_populates="planning_services")
    affectations: List["Affectation"] = Relationship(back_populates="planning_service")
    statut: Optional[StatutPlanning] = Relationship(back_populates="plannings")


# -------------------------
# Affectations & indisponibilités
# -------------------------
class Affectation(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_affectation"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    role: Optional[str] = None
    principal: bool = False
    presenceConfirmee: bool = False

    voix_code: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_voix.code", ondelete="CASCADE"), nullable=True)
    )

    instrument_code: Optional[str] = Field(
        sa_column=Column(
            ForeignKey("t_instrument.code", ondelete="CASCADE"), nullable=True
        )
    )

    planning_id: str = Field(
        sa_column=Column(
            ForeignKey("t_planningservice.id", ondelete="CASCADE"), nullable=False
        )
    )

    chantre_id: str = Field(
        sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False)
    )

    planning_service: Optional[PlanningService] = Relationship(
        back_populates="affectations"
    )
    chantre: Optional[Chantre] = Relationship(back_populates="affectations")
    voix: Optional[Voix] = Relationship(back_populates="affectations")
    instrument: Optional[Instrument] = Relationship(back_populates="affectations")


# -------------------------
# TABLE
# -------------------------
class Indisponibilite(IndisponibiliteBase, table=True):  # type: ignore
    __tablename__ = "t_indisponibilite"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )

    chantre_id: str = Field(
        sa_column=Column(
            ForeignKey("t_chantre.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    chantre: Optional[Chantre] = Relationship(back_populates="indisponibilites")


# -------------------------
# Responsabilités
# -------------------------
class Responsabilite(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_responsabilite"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    dateDebut: Optional[str] = None
    dateFin: Optional[str] = None
    actif: bool = True

    type_code: str = Field(
        sa_column=Column(
            ForeignKey("t_typeresponsabilite.code", ondelete="CASCADE"), nullable=False
        )
    )

    membre_id: str = Field(
        sa_column=Column(ForeignKey("t_membre.id", ondelete="CASCADE"), nullable=False)
    )

    ministere_id: Optional[str] = Field(
        sa_column=Column(
            ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=True
        )
    )

    pole_id: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_pole.id", ondelete="CASCADE"), nullable=True)
    )

    activite_id: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_activite.id", ondelete="CASCADE"), nullable=True)
    )

    membre: Optional[Membre] = Relationship(back_populates="responsabilites")
    ministere: Optional[Ministere] = Relationship()
    pole: Optional[Pole] = Relationship()
    activite: Optional[Activite] = Relationship(back_populates="responsabilites")
    type_responsabilite: Optional[TypeResponsabilite] = Relationship(
        back_populates="responsabilites"
    )


# -------------------------
# Utilisateurs & rôles
# -------------------------
class AffectationRole(AffectationRoleBase, table=True):  # type: ignore
    __tablename__ = "t_affectation_role"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    utilisateur_id: str = Field(
        sa_column=Column(
            ForeignKey("t_utilisateur.id", ondelete="CASCADE"), nullable=False
        )
    )

    role_id: str = Field(
        sa_column=Column(ForeignKey("t_role.id", ondelete="CASCADE"), nullable=False)
    )

    utilisateur: Optional["Utilisateur"] = Relationship(back_populates="affectations")
    role: Optional["Role"] = Relationship(back_populates="affectations")
    contextes: List["AffectationContexte"] = Relationship(back_populates="affectation")


class Utilisateur(UtilisateurBase, table=True):  # type: ignore
    __tablename__ = "t_utilisateur"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    password: str = Field(max_length=255)

    membre_id: Optional[str] = Field(
        sa_column=Column(
            ForeignKey("t_membre.id", ondelete="SET NULL"), nullable=True, unique=True
        )
    )

    membre: Optional["Membre"] = Relationship(
        back_populates="utilisateur", sa_relationship_kwargs={"uselist": False}
    )

    affectations: List["AffectationRole"] = Relationship(back_populates="utilisateur")


class RolePermission(SQLModel, table=True):  # type: ignore
    __tablename__ = "t_role_permission"

    role_id: str = Field(
        sa_column=Column(
            ForeignKey("t_role.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )

    permission_id: str = Field(
        sa_column=Column(
            ForeignKey("t_permission.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )


class Role(RoleBase, table=True):  # type: ignore
    __tablename__ = "t_role"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    affectations: List["AffectationRole"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermission
    )


class Permission(PermissionBase, table=True):  # type: ignore
    __tablename__ = "t_permission"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )
    code: str = Field(index=True, unique=True, max_length=100)

    roles: List["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )


# -------------------------
# Contextes
# -------------------------
class AffectationContexte(AffectationContexteBase, table=True):  # type: ignore
    __tablename__ = "t_affectation_contexte"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36
    )

    affectation_role_id: str = Field(
        sa_column=Column(
            ForeignKey("t_affectation_role.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    ministere_id: Optional[str] = Field(
        sa_column=Column(
            ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=True
        )
    )

    pole_id: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_pole.id", ondelete="CASCADE"), nullable=True)
    )

    activite_id: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_activite.id", ondelete="CASCADE"), nullable=True)
    )

    voix_id: Optional[str] = Field(
        sa_column=Column(ForeignKey("t_voix.code", ondelete="CASCADE"), nullable=True)
    )

    affectation: Optional["AffectationRole"] = Relationship(back_populates="contextes")
    ministere: Optional["Ministere"] = Relationship()
    pole: Optional["Pole"] = Relationship()
    activite: Optional["Activite"] = Relationship()
    voix: Optional["Voix"] = Relationship()


# -------------------------
# Export
# -------------------------
__all__ = [
    "Utilisateur",
    "RolePermission",
    "Permission",
    "AffectationContexte",
    "AffectationRole",
    "Role",
    "Voix",
    "Instrument",
    "StatutPlanning",
    "TypeResponsabilite",
    "OrganisationICC",
    "Pays",
    "Campus",
    "Ministere",
    "Pole",
    "Membre",
    "Chantre",
    "Choriste",
    "Musicien",
    "Equipe",
    "Equipe_Membre",
    "Activite",
    "PlanningService",
    "Affectation",
    "Indisponibilite",
    "Responsabilite",
]
