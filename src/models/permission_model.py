from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from .role_model import RoleRead


# -------------------------
# BASE
# -------------------------
class PermissionBase(SQLModel):
    code: str = Field(max_length=100)
    description: Optional[str] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str):
        if not v.strip():
            raise ValueError("Le code permission ne peut pas être vide")

        # Convention RBAC: RESOURCE_ACTION
        v = v.strip().upper()

        if " " in v:
            raise ValueError("Le code permission ne doit pas contenir d'espaces")

        if "_" not in v:
            raise ValueError(
                "Le code permission doit respecter la convention RESOURCE_ACTION"
            )

        return v


# -------------------------
# CREATE
# -------------------------
class PermissionCreate(PermissionBase):
    pass


# -------------------------
# READ
# -------------------------
class PermissionRead(PermissionBase):
    id: str
    roles: List["RoleRead"] = []


# -------------------------
# UPDATE
# -------------------------
class PermissionUpdate(SQLModel):
    code: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v is None:
            return v

        if not v.strip():
            raise ValueError("Le code permission ne peut pas être vide")

        v = v.strip().upper()

        if " " in v:
            raise ValueError("Le code permission ne doit pas contenir d'espaces")

        if "_" not in v:
            raise ValueError(
                "Le code permission doit respecter la convention RESOURCE_ACTION"
            )

        return v


__all__ = ["PermissionBase", "PermissionCreate", "PermissionRead", "PermissionUpdate"]
