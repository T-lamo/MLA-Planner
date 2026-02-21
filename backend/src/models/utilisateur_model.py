from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from models.role_model import RoleRead


class UtilisateurBase(SQLModel):
    username: str = Field(max_length=50)
    actif: bool = True


class UtilisateurCreate(UtilisateurBase):
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    roles_ids: List[int] = []

    @field_validator("username")
    @classmethod
    def no_blank_username(cls, v: str):
        if not v.strip():
            raise ValueError("Le nom d'utilisateur ne peut pas être vide")
        return v

    @field_validator("roles_ids")
    @classmethod
    def unique_roles(cls, v: List[str]):
        if len(set(v)) != len(v):
            raise ValueError("Les rôles ne doivent pas contenir de doublons")
        return v


class UtilisateurRead(UtilisateurBase):
    id: str
    membre_id: Optional[str] = None  # Relation
    roles: List[RoleRead] = []

    # password n’est jamais exposé


class UtilisateurUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    actif: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    roles_ids: Optional[List[int]] = None

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Le nom d'utilisateur ne peut pas être vide")
        return v

    @field_validator("roles_ids")
    @classmethod
    def roles_valid(cls, v):
        if v is None:
            return v

        if len(v) == 0:
            raise ValueError("L'utilisateur doit avoir au moins un rôle")

        if 0 in v:
            raise ValueError("Le rôle 0 est invalide")

        if len(set(v)) != len(v):
            raise ValueError("Les rôles ne doivent pas contenir de doublons")

        return v


__all__ = [
    "UtilisateurBase",
    "UtilisateurCreate",
    "UtilisateurRead",
    "UtilisateurUpdate",
]
