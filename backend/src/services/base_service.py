from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

# Remplacement des exceptions standards par AppException
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models.base_pagination import PaginatedResponse

C = TypeVar("C", bound=SQLModel)
R = TypeVar("R", bound=SQLModel)
U = TypeVar("U", bound=SQLModel)
T = TypeVar("T", bound=SQLModel)


class BaseService(Generic[C, R, U, T]):
    def __init__(self, repo: Any, resource_name: str = "Resource"):
        self.repo = repo
        self.resource_name = resource_name

    def get_one(self, identifiant: str) -> T:
        obj = self.repo.get_by_id(identifiant)
        if not obj:
            # Utilisation du code CORE_001 avec injection du nom de ressource
            raise AppException(
                ErrorRegistry.CORE_RESOURCE_NOT_FOUND, resource=self.resource_name
            )
        return obj

    def list_paginated(self, limit: int, offset: int) -> PaginatedResponse[R]:
        items = self.repo.get_paginated(limit, offset)
        total = self.repo.count()
        return PaginatedResponse(total=total, limit=limit, offset=offset, data=items)

    def delete(self, identifiant: str) -> None:
        obj = self.get_one(identifiant)

        update_data: dict[str, Any] = {}
        if hasattr(obj, "deleted_at"):
            update_data["deleted_at"] = datetime.now()

        for field in ["actif", "active"]:
            if hasattr(obj, field):
                update_data[field] = False
        try:
            self.repo.update(obj, update_data)
            self._after_delete_hook(obj)
        except IntegrityError as exc:
            raise AppException(
                ErrorRegistry.CORE_ACTION_IMPOSSIBLE, resource=self.resource_name
            ) from exc

    def create(self, data: C) -> T:
        db_obj = self.repo.model.model_validate(data)
        return self.repo.create(db_obj)

    def update(self, identifiant: str, data: U) -> T:
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)
        return self.repo.update(obj, update_data)

    def _after_delete_hook(self, obj: T) -> None:
        """
        Hook destiné à être surchargé dans les services enfants
        pour gérer les cascades spécifiques.
        """
