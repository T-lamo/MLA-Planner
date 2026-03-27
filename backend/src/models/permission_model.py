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
    def normalize_code(cls, v: str) -> str:
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
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
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


class PermissionCodeRead(SQLModel):
    """Version légère sans relation inverse (évite les refs circulaires)."""

    id: str
    code: str


class RoleWithPermissionsRead(SQLModel):
    """Rôle avec la liste de ses permissions — usage admin uniquement."""

    id: str
    libelle: Optional[str] = None
    permissions: List[PermissionCodeRead] = []


class RolePermissionsUpdate(SQLModel):
    """Remplace les permissions d'un rôle (liste complète des codes)."""

    permission_codes: List[str]


class RoleCreate(SQLModel):
    """Crée un nouveau rôle applicatif."""

    libelle: str = Field(max_length=100)

    @field_validator("libelle")
    @classmethod
    def normalize_libelle(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le libellé ne peut pas être vide")
        return v


class CapabilityCreate(PermissionBase):
    """Crée une nouvelle capability (hérite de la validation RESOURCE_ACTION)."""


__all__ = [
    "CapabilityCreate",
    "PermissionBase",
    "PermissionCodeRead",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
    "RoleCreate",
    "RolePermissionsUpdate",
    "RoleWithPermissionsRead",
]
