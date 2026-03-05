from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# Ce modèle permet de réutiliser la structure "data" partout
class DataListResponse(BaseModel, Generic[T]):
    data: List[T]


class DataResponse(BaseModel, Generic[T]):
    data: T


__all__ = ["DataListResponse", "DataResponse"]
