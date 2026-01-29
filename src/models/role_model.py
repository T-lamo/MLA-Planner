from typing import Optional

from sqlmodel import Field, SQLModel

from mla_enum import RoleName


class RoleBase(SQLModel):
    libelle: RoleName | None = Field(unique=True, nullable=False)


class RoleUpdate(RoleBase):
    libelle: Optional[RoleName] = None


class RoleRead(RoleBase):
    id: str


__all__ = ["RoleBase", "RoleRead", "RoleUpdate", "RoleName"]
