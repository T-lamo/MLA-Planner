from typing import Generic, List, TypeVar

from sqlmodel import SQLModel

# Déclaration d'une variable de type générique
T = TypeVar("T")


class PaginatedResponse(SQLModel, Generic[T]):
    total: int
    limit: int
    offset: int
    data: List[T]
    model_config = {"from_attributes": True}
