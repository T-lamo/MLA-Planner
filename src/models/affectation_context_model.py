from typing import Optional

from pydantic import field_validator
from sqlmodel import SQLModel


# -------------------------
# BASE
# -------------------------
class AffectationContexteBase(SQLModel):
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None
    activite_id: Optional[str] = None
    voix_id: Optional[str] = None

    @field_validator("*")
    @classmethod
    def at_least_one_context(cls, v, info):
        """
        Validation métier :
        Une affectation doit cibler au moins un contexte
        """
        data = info.data
        if not any(
            [
                data.get("ministere_id"),
                data.get("pole_id"),
                data.get("activite_id"),
                data.get("voix_id"),
            ]
        ):
            raise ValueError(
                "Au moins un contexte doit être défini "
                "(ministere, pole, activite ou voix)"
            )
        return v


# -------------------------
# CREATE
# -------------------------
class AffectationContexteCreate(AffectationContexteBase):
    affectation_id: str


# -------------------------
# READ
# -------------------------
class AffectationContexteRead(AffectationContexteBase):
    id: str
    affectation_id: str


# -------------------------
# UPDATE
# -------------------------
class AffectationContexteUpdate(SQLModel):
    ministere_id: Optional[str] = None
    pole_id: Optional[str] = None
    activite_id: Optional[str] = None
    voix_id: Optional[str] = None

    @field_validator("*")
    @classmethod
    def validate_context_update(cls, v, info):
        data = info.data
        if not any(
            [
                data.get("ministere_id"),
                data.get("pole_id"),
                data.get("activite_id"),
                data.get("voix_id"),
            ]
        ):
            raise ValueError("Au moins un contexte doit rester défini")
        return v


__all__ = [
    "AffectationContexteBase",
    "AffectationContexteCreate",
    "AffectationContexteRead",
    "AffectationContexteUpdate",
]
