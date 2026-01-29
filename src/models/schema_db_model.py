# models.py
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from .utilisateur_model import UtilisateurBase
from .membre_model import MembreBase
from .role_model import RoleBase
import uuid
from sqlalchemy import Column, ForeignKey

# -------------------------
# Tables de référence (Enums)
# -------------------------
class Voix(SQLModel, table=True):
    __tablename__ = "t_voix"
    code: str = Field(primary_key=True, max_length=20)
    choristes: List["Choriste"] = Relationship(back_populates="voix")
    affectations: List["Affectation"] = Relationship(back_populates="voix")

class Instrument(SQLModel, table=True):
    __tablename__ = "t_instrument"
    code: str = Field(primary_key=True, max_length=20)
    musiciens: List["Musicien"] = Relationship(back_populates="instrument")
    affectations: List["Affectation"] = Relationship(back_populates="instrument")

class StatutPlanning(SQLModel, table=True):
    __tablename__ = "t_statutplanning"
    code: str = Field(primary_key=True, max_length=20)
    plannings: List["PlanningService"] = Relationship(back_populates="statut")

class TypeResponsabilite(SQLModel, table=True):
    __tablename__ = "t_typeresponsabilite"
    code: str = Field(primary_key=True, max_length=50)
    responsabilites: List["Responsabilite"] = Relationship(back_populates="type_responsabilite")

# -------------------------
# Tables principales
# -------------------------
class OrganisationICC(SQLModel, table=True):
    __tablename__ = "t_organisationicc"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    dateCreation: str
    pays: List["Pays"] = Relationship(back_populates="organisation")

class Pays(SQLModel, table=True):
    __tablename__ = "t_pays"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    code: str
    organisation_id: str = Field(sa_column=Column(ForeignKey("t_organisationicc.id", ondelete="CASCADE"), nullable=False))
    organisation: Optional[OrganisationICC] = Relationship(back_populates="pays")
    campus: List["Campus"] = Relationship(back_populates="pays")

class Campus(SQLModel, table=True):
    __tablename__ = "t_campus"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    ville: str
    timezone: str
    pays_id: str = Field(sa_column=Column(ForeignKey("t_pays.id", ondelete="CASCADE"), nullable=False))
    pays: Optional[Pays] = Relationship(back_populates="campus")
    ministeres: List["Ministere"] = Relationship(back_populates="campus")
    activites: List["Activite"] = Relationship(back_populates="campus")

class Ministere(SQLModel, table=True):
    __tablename__ = "t_ministere"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    dateCreation: str
    actif: bool = True
    campus_id: str = Field(sa_column=Column(ForeignKey("t_campus.id", ondelete="CASCADE"), nullable=False))
    campus: Optional[Campus] = Relationship(back_populates="ministeres")
    poles: List["Pole"] = Relationship(back_populates="ministere")
    membres: List["Membre"] = Relationship(back_populates="ministere")
    equipes: List["Equipe"] = Relationship(back_populates="ministere")

class Pole(SQLModel, table=True):
    __tablename__ = "t_pole"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    description: Optional[str] = None
    ministere_id: str = Field(sa_column=Column(ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False))
    ministere: Optional[Ministere] = Relationship(back_populates="poles")
    membres: List["Membre"] = Relationship(back_populates="pole")

# -------------------------
# Utilisateurs & Rôles
# -------------------------
class RoleUtilisateur(SQLModel, table=True):
    __tablename__ = "t_utilisateur_role"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    utilisateur_id: str | None = Field(sa_column=Column(ForeignKey("t_utilisateur.id", ondelete="CASCADE"), nullable=True))
    role_id: str | None = Field(sa_column=Column(ForeignKey("t_role.id", ondelete="CASCADE"), nullable=True))

class Utilisateur(UtilisateurBase, table=True):
    __tablename__ = "t_utilisateur"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    password: str = Field(max_length=255)
    membre_id: str | None = Field(sa_column=Column(ForeignKey("t_membre.id", ondelete="SET NULL"), nullable=True, unique=True))
    membre: Optional["Membre"] = Relationship(back_populates="utilisateur", sa_relationship_kwargs={"uselist": False})
    roles: List["Role"] = Relationship(back_populates="utilisateurs", link_model=RoleUtilisateur)

class Role(RoleBase, table=True):
    __tablename__ = "t_role"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    utilisateurs: List["Utilisateur"] = Relationship(back_populates="roles", link_model=RoleUtilisateur)

# -------------------------
# Membres et liens
# -------------------------
class Membre(MembreBase, table=True):
    __tablename__ = "t_membre"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    dateInscription: Optional[str] = None
    ministere_id: str = Field(sa_column=Column(ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False))
    pole_id: str = Field(sa_column=Column(ForeignKey("t_pole.id", ondelete="CASCADE"), nullable=False))
    ministere: Optional[Ministere] = Relationship(back_populates="membres")
    pole: Optional[Pole] = Relationship(back_populates="membres")
    chantres: List["Chantre"] = Relationship(back_populates="membre")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="membre")
    equipes_assoc: List["Equipe_Membre"] = Relationship(back_populates="membre")
    utilisateur: Optional["Utilisateur"] = Relationship(back_populates="membre", sa_relationship_kwargs={"uselist": False})

# -------------------------
# Choristes, Musiciens et équipes
# -------------------------
class Chantre(SQLModel, table=True):
    __tablename__ = "t_chantre"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    dateIntegration: Optional[str] = None
    niveau: Optional[str] = None
    membre_id: str = Field(sa_column=Column(ForeignKey("t_membre.id", ondelete="CASCADE"), nullable=False))
    membre: Optional[Membre] = Relationship(back_populates="chantres")
    choristes: List["Choriste"] = Relationship(back_populates="chantre")
    musiciens: List["Musicien"] = Relationship(back_populates="chantre")
    affectations: List["Affectation"] = Relationship(back_populates="chantre")
    indisponibilites: List["Indisponibilite"] = Relationship(back_populates="chantre")

class Choriste(SQLModel, table=True):
    __tablename__ = "t_choriste"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    voix_code: str = Field(sa_column=Column(ForeignKey("t_voix.code", ondelete="CASCADE"), nullable=False))
    secondaireVoix: Optional[str] = None
    chantre_id: str = Field(sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False))
    chantre: Optional[Chantre] = Relationship(back_populates="choristes")
    voix: Optional[Voix] = Relationship(back_populates="choristes")

class Musicien(SQLModel, table=True):
    __tablename__ = "t_musicien"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    instrument_code: str = Field(sa_column=Column(ForeignKey("t_instrument.code", ondelete="CASCADE"), nullable=False))
    instrumentPrincipal: Optional[str] = None
    chantre_id: str = Field(sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False))
    chantre: Optional[Chantre] = Relationship(back_populates="musiciens")
    instrument: Optional[Instrument] = Relationship(back_populates="musiciens")

# -------------------------
# Équipes
# -------------------------
class Equipe(SQLModel, table=True):
    __tablename__ = "t_equipe"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    nom: str
    active: bool = True
    ministere_id: str = Field(sa_column=Column(ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=False))
    ministere: Optional[Ministere] = Relationship(back_populates="equipes")
    membres_assoc: List["Equipe_Membre"] = Relationship(back_populates="equipe")

class Equipe_Membre(SQLModel, table=True):
    __tablename__ = "t_equipe_membre"
    equipe_id: str = Field(sa_column=Column(ForeignKey("t_equipe.id", ondelete="CASCADE"), primary_key=True))
    membre_id: str = Field(sa_column=Column(ForeignKey("t_membre.id", ondelete="CASCADE"), primary_key=True))
    equipe: Optional[Equipe] = Relationship(back_populates="membres_assoc")
    membre: Optional[Membre] = Relationship(back_populates="equipes_assoc")

# -------------------------
# Activités, Planning et Affectations
# -------------------------
class Activite(SQLModel, table=True):
    __tablename__ = "t_activite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    type: Optional[str] = None
    dateDebut: Optional[str] = None
    dateFin: Optional[str] = None
    lieu: Optional[str] = None
    description: Optional[str] = None
    campus_id: str = Field(sa_column=Column(ForeignKey("t_campus.id", ondelete="CASCADE"), nullable=False))
    campus: Optional[Campus] = Relationship(back_populates="activites")
    planning_services: List["PlanningService"] = Relationship(back_populates="activite")
    responsabilites: List["Responsabilite"] = Relationship(back_populates="activite")

class PlanningService(SQLModel, table=True):
    __tablename__ = "t_planningservice"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    statut_code: str = Field(sa_column=Column(ForeignKey("t_statutplanning.code", ondelete="CASCADE"), nullable=False))
    dateCreation: Optional[str] = None
    activite_id: str = Field(sa_column=Column(ForeignKey("t_activite.id", ondelete="CASCADE"), nullable=False))
    activite: Optional[Activite] = Relationship(back_populates="planning_services")
    affectations: List["Affectation"] = Relationship(back_populates="planning_service")
    statut: Optional[StatutPlanning] = Relationship(back_populates="plannings")

class Affectation(SQLModel, table=True):
    __tablename__ = "t_affectation"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    role: Optional[str] = None
    voix_code: Optional[str] = Field(sa_column=Column(ForeignKey("t_voix.code", ondelete="CASCADE")))
    instrument_code: Optional[str] = Field(sa_column=Column(ForeignKey("t_instrument.code", ondelete="CASCADE")))
    principal: bool = False
    presenceConfirmee: bool = False
    planning_id: str = Field(sa_column=Column(ForeignKey("t_planningservice.id", ondelete="CASCADE"), nullable=False))
    chantre_id: str = Field(sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False))
    planning_service: Optional[PlanningService] = Relationship(back_populates="affectations")
    chantre: Optional[Chantre] = Relationship(back_populates="affectations")
    voix: Optional[Voix] = Relationship(back_populates="affectations")
    instrument: Optional[Instrument] = Relationship(back_populates="affectations")

class Indisponibilite(SQLModel, table=True):
    __tablename__ = "t_indisponibilite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    dateDebut: Optional[str] = None
    dateFin: Optional[str] = None
    motif: Optional[str] = None
    validee: bool = False
    chantre_id: str = Field(sa_column=Column(ForeignKey("t_chantre.id", ondelete="CASCADE"), nullable=False))
    chantre: Optional[Chantre] = Relationship(back_populates="indisponibilites")

class Responsabilite(SQLModel, table=True):
    __tablename__ = "t_responsabilite"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    type_code: str = Field(sa_column=Column(ForeignKey("t_typeresponsabilite.code", ondelete="CASCADE"), nullable=False))
    dateDebut: Optional[str] = None
    dateFin: Optional[str] = None
    actif: bool = True
    membre_id: str = Field(sa_column=Column(ForeignKey("t_membre.id", ondelete="CASCADE"), nullable=False))
    ministere_id: Optional[str] = Field(sa_column=Column(ForeignKey("t_ministere.id", ondelete="CASCADE"), nullable=True))
    pole_id: Optional[str] = Field(sa_column=Column(ForeignKey("t_pole.id", ondelete="CASCADE"), nullable=True))
    activite_id: Optional[str] = Field(sa_column=Column(ForeignKey("t_activite.id", ondelete="CASCADE"), nullable=True))
    membre: Optional[Membre] = Relationship(back_populates="responsabilites")
    ministere: Optional[Ministere] = Relationship()
    pole: Optional[Pole] = Relationship()
    activite: Optional[Activite] = Relationship(back_populates="responsabilites")
    type_responsabilite: Optional[TypeResponsabilite] = Relationship(back_populates="responsabilites")

# -------------------------
# Export all models
# -------------------------
__all__ = [
    "Utilisateur",
    "Role",
    "RoleUtilisateur",
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
