from datetime import date
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class ChantreBase(SQLModel):
    dateIntegration: Optional[date] = Field(
        default=None, description="Date d'intégration du chantre"
    )

    niveau: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Niveau du chantre (ex: Débutant, Intermédiaire, Avancé)",
    )

    membre_id: str = Field(
        min_length=36,
        max_length=36,
        description="UUID du membre associé",
    )


# ======================
# CREATE
# ======================
class ChantreCreate(ChantreBase):
    """
    Tous les champs requis à la création
    """


# ======================
# UPDATE
# ======================
class ChantreUpdate(SQLModel):
    dateIntegration: Optional[date] = None
    niveau: Optional[str] = Field(None, min_length=2, max_length=50)


# ======================
# READ
# ======================
class ChantreRead(ChantreBase):
    id: str
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = [
    "ChantreBase",
    "ChantreCreate",
    "ChantreUpdate",
    "ChantreRead",
]
