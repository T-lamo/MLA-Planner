"""
Modèles SQLModel et schémas Pydantic pour le module Songbook.

Tables créées :
  t_chant_categorie  — catégories de chants (code PK, ordre)
  t_chant            — chants (titre, artiste nullable, campus FK)
  t_chant_contenu    — contenu ChordPro versionné (1 par chant)
  t_chant_artiste_link — artistes crédités supplémentaires (M:N dénormalisé)
  t_chant_tag        — étiquettes libres
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import ConfigDict, field_validator
from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel

_YOUTUBE_RE = re.compile(
    r"^https?://(?:www\.|m\.)?(?:youtube\.com/"
    r"(?:watch\?[^&]*v=|embed/|shorts/)|youtu\.be/)"
    r"[A-Za-z0-9_-]{11}"
)

# -------------------------
# BASE MODELS
# -------------------------


class ChantCategorieBase(SQLModel):
    """Catégorie de chant (Gospel, Cantique, Louange…)."""

    libelle: str = Field(max_length=100)
    ordre: int = Field(default=0)
    description: Optional[str] = Field(default=None)


class ChantBase(SQLModel):
    """Champ communs d'un chant."""

    titre: str = Field(max_length=200)
    artiste: Optional[str] = Field(default=None, max_length=150)
    campus_id: str = Field(foreign_key="t_campus.id", ondelete="CASCADE")
    categorie_code: Optional[str] = Field(
        default=None,
        foreign_key="t_chant_categorie.code",
        ondelete="SET NULL",
    )
    actif: bool = Field(default=True)
    youtube_url: Optional[str] = Field(default=None, max_length=500)


class ChantContenuBase(SQLModel):
    """Contenu ChordPro versionné d'un chant."""

    tonalite: str = Field(max_length=10)
    paroles_chords: str = Field(sa_column=Column(Text, nullable=False))
    version: int = Field(default=1)


class ChantTagBase(SQLModel):
    """Étiquette libre associée à un chant."""

    libelle: str = Field(max_length=50)


# -------------------------
# TABLE MODELS
# -------------------------


class ChantCategorie(ChantCategorieBase, table=True):  # type: ignore
    """Table t_chant_categorie."""

    __tablename__ = "t_chant_categorie"
    __table_args__ = {"extend_existing": True}

    code: str = Field(primary_key=True, max_length=30)
    chants: List["Chant"] = Relationship(back_populates="categorie")


class Chant(ChantBase, table=True):  # type: ignore
    """Table t_chant — isolation multi-tenant via campus_id."""

    __tablename__ = "t_chant"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date_creation: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    categorie: Optional[ChantCategorie] = Relationship(back_populates="chants")
    contenu: Optional["ChantContenu"] = Relationship(
        back_populates="chant",
        sa_relationship_kwargs={"uselist": False},
    )
    artistes_assoc: List["ChantArtisteLink"] = Relationship(back_populates="chant")
    tags: List["ChantTag"] = Relationship(back_populates="chant")


class ChantContenu(ChantContenuBase, table=True):  # type: ignore
    """Table t_chant_contenu — un enregistrement par chant (unique FK)."""

    __tablename__ = "t_chant_contenu"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    chant_id: str = Field(foreign_key="t_chant.id", unique=True, ondelete="CASCADE")
    date_modification: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    chant: Optional[Chant] = Relationship(back_populates="contenu")


class ChantArtisteLink(SQLModel, table=True):  # type: ignore
    """Table t_chant_artiste_link — crédits artistes supplémentaires."""

    __tablename__ = "t_chant_artiste_link"
    __table_args__ = {"extend_existing": True}

    chant_id: str = Field(
        foreign_key="t_chant.id", primary_key=True, ondelete="CASCADE"
    )
    artiste_nom: str = Field(primary_key=True, max_length=150)
    role: str = Field(default="INTERPRETE", max_length=50)

    chant: Optional[Chant] = Relationship(back_populates="artistes_assoc")


class ChantTag(ChantTagBase, table=True):  # type: ignore
    """Table t_chant_tag — étiquettes libres."""

    __tablename__ = "t_chant_tag"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    chant_id: str = Field(foreign_key="t_chant.id", ondelete="CASCADE")

    chant: Optional[Chant] = Relationship(back_populates="tags")


# -------------------------
# PYDANTIC SCHEMAS
# -------------------------


class ChantCategorieRead(SQLModel):
    """Schéma de lecture d'une catégorie de chant."""

    model_config = ConfigDict(from_attributes=True)  # type: ignore

    code: str
    libelle: str
    ordre: int
    description: Optional[str]


class ChantCategorieCreate(SQLModel):
    """Payload de création d'une catégorie de chant."""

    code: str = Field(max_length=30)
    libelle: str = Field(max_length=100)
    ordre: int = 0
    description: Optional[str] = None


class ChantCategorieUpdate(SQLModel):
    """Payload de mise à jour partielle d'une catégorie."""

    libelle: Optional[str] = None
    ordre: Optional[int] = None
    description: Optional[str] = None


class ChantRead(SQLModel):
    """Schéma de lecture d'un chant (liste)."""

    model_config = ConfigDict(from_attributes=True)  # type: ignore

    id: str
    titre: str
    artiste: Optional[str]
    campus_id: str
    categorie_code: Optional[str]
    actif: bool
    date_creation: datetime
    youtube_url: Optional[str] = None


class ChantCreate(SQLModel):
    """Payload de création d'un chant."""

    titre: str = Field(max_length=200)
    artiste: Optional[str] = Field(default=None, max_length=150)
    campus_id: str
    categorie_code: Optional[str] = None
    youtube_url: Optional[str] = None

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, v: Optional[str]) -> Optional[str]:
        """Valide que l'URL est bien une URL YouTube reconnue."""
        if v is None:
            return None
        stripped = v.strip()
        if not _YOUTUBE_RE.match(stripped):
            raise ValueError("URL YouTube invalide")
        return stripped


class ChantUpdate(SQLModel):
    """Payload de mise à jour partielle d'un chant."""

    titre: Optional[str] = None
    artiste: Optional[str] = None
    categorie_code: Optional[str] = None
    youtube_url: Optional[str] = None

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, v: Optional[str]) -> Optional[str]:
        """Valide que l'URL est bien une URL YouTube reconnue."""
        if v is None:
            return None
        stripped = v.strip()
        if not _YOUTUBE_RE.match(stripped):
            raise ValueError("URL YouTube invalide")
        return stripped


class ChantContenuRead(SQLModel):
    """Schéma de lecture du contenu ChordPro."""

    model_config = ConfigDict(from_attributes=True)  # type: ignore

    id: str
    chant_id: str
    tonalite: str
    paroles_chords: str
    version: int
    date_modification: datetime


class ChantContenuCreate(SQLModel):
    """Payload de création du contenu ChordPro."""

    tonalite: str = Field(max_length=10)
    paroles_chords: str


class ChantContenuUpdate(SQLModel):
    """Payload de mise à jour du contenu — version obligatoire (OCC)."""

    tonalite: Optional[str] = None
    paroles_chords: Optional[str] = None
    version: int


class ChantReadFull(ChantRead):
    """Chant avec contenu et catégorie chargés."""

    contenu: Optional[ChantContenuRead] = None
    categorie: Optional[ChantCategorieRead] = None


class ChantTransposeRequest(SQLModel):
    """Requête de transposition (sans sauvegarde)."""

    semitones: int = Field(ge=-12, le=12)


class ChantTransposeResponse(SQLModel):
    """Résultat de transposition."""

    tonalite_originale: str
    tonalite_transposee: str
    paroles_chords: str


__all__ = [
    "ChantCategorie",
    "ChantCategorieBase",
    "ChantCategorieCreate",
    "ChantCategorieRead",
    "ChantCategorieUpdate",
    "Chant",
    "ChantBase",
    "ChantCreate",
    "ChantRead",
    "ChantReadFull",
    "ChantUpdate",
    "ChantContenu",
    "ChantContenuBase",
    "ChantContenuCreate",
    "ChantContenuRead",
    "ChantContenuUpdate",
    "ChantArtisteLink",
    "ChantTag",
    "ChantTagBase",
    "ChantTransposeRequest",
    "ChantTransposeResponse",
]
