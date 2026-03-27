from typing import Optional

from sqlmodel import Field, SQLModel


class RoleBase(SQLModel):
    libelle: str | None = Field(max_length=100, unique=True, nullable=False)


class RoleUpdate(RoleBase):
    libelle: Optional[str] = None


class RoleRead(RoleBase):
    id: str


__all__ = ["RoleBase", "RoleRead", "RoleUpdate"]
