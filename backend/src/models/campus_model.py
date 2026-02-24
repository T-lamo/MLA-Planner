from typing import TYPE_CHECKING, List, Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from membre_model import MembreRead


# -------------------------
# BASE
# -------------------------
class CampusBase(SQLModel):
    nom: str = Field(
        index=True, min_length=2, max_length=100, description="Nom du campus"
    )
    ville: str = Field(
        min_length=2, max_length=100, description="Ville où se situe le campus"
    )
    timezone: str = Field(
        default="Europe/Paris", description="Fuseau horaire (ex: Africa/Abidjan)"
    )

    @field_validator("nom", "ville")
    @classmethod
    def not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip()


# -------------------------
# CREATE
# -------------------------
class CampusCreate(CampusBase):
    pays_id: str = Field(max_length=36, description="UUID du pays rattaché")


# -------------------------
# UPDATE
# -------------------------
class CampusUpdate(SQLModel):
    nom: Optional[str] = None
    ville: Optional[str] = None
    timezone: Optional[str] = None
    pays_id: Optional[str] = None


# -------------------------
# READ
# -------------------------
class CampusRead(CampusBase):
    id: str
    pays_id: str
    membres: List["MembreRead"] = []
    model_config = ConfigDict(from_attributes=True)  # type: ignore

    # Note : On inclut généralement PaysRead ici si importé,
    # sinon on reste sur les types simples pour éviter les cycles.


__all__ = [
    "CampusBase",
    "CampusUpdate",
    "CampusRead",
    "CampusCreate",
]
