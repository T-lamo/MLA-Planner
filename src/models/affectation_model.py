from typing import Optional

from sqlmodel import Field, SQLModel


class AffectationBase(SQLModel):
    slot_id: str = Field(foreign_key="t_slot.id", ondelete="CASCADE")
    membre_id: str = Field(foreign_key="t_membre.id", ondelete="CASCADE")
    role_code: str = Field(max_length=50)
    statut_affectation_code: str = Field(foreign_key="t_statutaffectation.code")
    presence_confirmee: bool = Field(default=False)


class AffectationUpdate(SQLModel):
    role_code: Optional[str] = Field(default=None, max_length=50)
    statut_affectation_code: Optional[str] = Field(default=None)
    presence_confirmee: Optional[bool] = None


class AffectationCreate(AffectationBase):
    pass


class AffectationRead(AffectationBase):
    id: str


__all__ = [
    "AffectationBase",
    "AffectationCreate",
    "AffectationRead",
    "AffectationUpdate",
]
