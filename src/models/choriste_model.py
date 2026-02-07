import uuid
from typing import List, Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, SQLModel

from models.choriste_voix_model import ChoristeVoixCreate, ChoristeVoixRead


# -------------------------
# CHORISTE BASE
# -------------------------
class ChoristeBase(SQLModel):
    chantre_id: uuid.UUID = Field(description="UUID du chantre rattaché")


# -------------------------
# CREATE
# -------------------------
class ChoristeCreate(ChoristeBase):
    # On s'attend à recevoir une liste d'objets voix à la création
    voix_assoc: List[ChoristeVoixCreate]

    @field_validator("voix_assoc")
    @classmethod
    def validate_unique_principal(cls, v: List[ChoristeVoixCreate]):
        if not v:
            raise ValueError("Un choriste doit être assigné à au moins une voix.")

        principales = [voix for voix in v if voix.is_principal]
        if len(principales) == 0:
            raise ValueError("Le choriste doit avoir exactement une voix principale.")
        if len(principales) > 1:
            raise ValueError(
                "Un choriste ne peut pas avoir plusieurs voix principales."
            )
        return v


# -------------------------
# UPDATE
# -------------------------
class ChoristeUpdate(SQLModel):
    # Optionnel car on peut vouloir changer seulement le chantre_id
    chantre_id: Optional[uuid.UUID] = None
    # Pour l'update des voix, on remplace généralement la liste complète
    voix_assoc: Optional[List[ChoristeVoixCreate]] = None

    @model_validator(mode="after")
    def check_update_integrity(self) -> "ChoristeUpdate":
        if self.voix_assoc is not None:
            principales = [v for v in self.voix_assoc if v.is_principal]
            if len(principales) != 1:
                raise ValueError(
                    "La mise à jour doit inclure exactement une voix principale."
                )
        return self


# -------------------------
# READ
# -------------------------
class ChoristeRead(ChoristeBase):
    id: uuid.UUID
    # On renvoie la liste des voix associées
    voix_assoc: List[ChoristeVoixRead] = []

    # Propriété calculée pour faciliter l'usage au Front-end
    @property
    def voix_principale(self) -> Optional[str]:
        for assoc in self.voix_assoc:
            if assoc.is_principal:
                return assoc.voix_code
        return None


__all__ = ["ChoristeBase", "ChoristeCreate", "ChoristeUpdate", "ChoristeRead"]
