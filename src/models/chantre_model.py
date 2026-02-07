import uuid
from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel

from mla_enum.custom_enum import NiveauChantre


# -------------------------
# BASE
# -------------------------
class ChantreBase(SQLModel):
    # Changement en snake_case
    date_integration: Optional[date] = Field(
        default=None, description="Date d'intégration du chantre"
    )

    niveau: Optional[NiveauChantre] = Field(
        default=NiveauChantre.DEBUTANT,
        description="Niveau technique (Débutant, Intermédiaire, Avancé)",
    )

    # UUID natif pour une meilleure performance SQL
    membre_id: uuid.UUID = Field(
        foreign_key="t_membre.id",
        description="UUID du membre associé",
    )


# -------------------------
# CREATE
# -------------------------
class ChantreCreate(ChantreBase):
    """Tous les champs requis à la création."""


# -------------------------
# UPDATE
# -------------------------
class ChantreUpdate(SQLModel):
    """Permet de modifier chaque champ optionnellement."""

    date_integration: Optional[date] = None
    niveau: Optional[NiveauChantre] = None


# -------------------------
# READ
# -------------------------
class ChantreRead(ChantreBase):
    id: uuid.UUID

    # Relations (Optionnelles dans le JSON pour éviter les réponses trop lourdes)
    # choristes: List[Choriste] = []
    # musiciens: List[Musicien] = []
    # affectations: List[Aff] = []
    # indisponibilites: List[dict] = []

    # @computed_field  # type: ignore[misc]
    # @property
    # def choristes_count(self) -> int:
    #     return len(self.choristes)

    # @computed_field  # type: ignore[misc]
    # @property
    # def musiciens_count(self) -> int:
    #     return len(self.musiciens)

    # @computed_field  # type: ignore[misc]
    # @property
    # def affectations_count(self) -> int:
    #     return len(self.affectations)


__all__ = [
    "ChantreBase",
    "ChantreCreate",
    "ChantreUpdate",
    "ChantreRead",
]
