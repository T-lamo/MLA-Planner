from typing import Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel


# -------------------------
# BASE
# -------------------------
class MembreRoleBase(SQLModel):
    membre_id: str = Field(
        foreign_key="t_membre.id", primary_key=True, description="UUID du membre"
    )
    role_code: str = Field(
        foreign_key="t_rolecompetence.code",
        primary_key=True,
        description="Code du rôle",
    )
    niveau: str = Field(default="DEBUTANT", description="Niveau de compétence")
    is_principal: bool = Field(default=False)

    @field_validator("niveau")
    @classmethod
    def validate_niveau(cls, v: str):
        allowed = ["DEBUTANT", "INTERMEDIAIRE", "AVANCE", "EXPERT"]
        v = v.strip().upper()
        if v not in allowed:
            raise ValueError(f"Le niveau doit être parmi : {', '.join(allowed)}")
        return v

    @field_validator("role_code")
    @classmethod
    def clean_code(cls, v: str):
        return v.strip().upper()


# -------------------------
# CREATE
# -------------------------
class MembreRoleCreate(MembreRoleBase):
    pass


# -------------------------
# UPDATE
# -------------------------
class MembreRoleUpdate(SQLModel):
    niveau: Optional[str] = None
    is_principal: Optional[bool] = None


# -------------------------
# READ
# -------------------------
class MembreRoleRead(MembreRoleBase):
    model_config = ConfigDict(from_attributes=True)  # type: ignore


__all__ = [
    "MembreRoleBase",
    "MembreRoleCreate",
    "MembreRoleUpdate",
    "MembreRoleRead",
]
