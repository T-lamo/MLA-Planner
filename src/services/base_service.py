from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from core.exceptions import BadRequestException, NotFoundException
from models.base_pagination import PaginatedResponse

# C: Schéma Create (ex: PaysCreate)
# R: Schéma Read (ex: PaysRead)
# U: Schéma Update (ex: PaysUpdate)
# T: Modèle DB (ex: Pays)
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
            raise NotFoundException(f"{self.resource_name} introuvable.")
        return obj

    def list_paginated(self, limit: int, offset: int) -> PaginatedResponse[R]:
        """Retourne une réponse paginée utilisant le type de lecture R."""
        items = self.repo.get_paginated(limit, offset)
        total = self.repo.count()

        return PaginatedResponse[R](total=total, limit=limit, offset=offset, data=items)

    def delete(self, identifiant: str) -> None:
        """Logique de Soft Delete générique."""
        obj = self.get_one(identifiant)

        update_data: dict[str, Any] = {}
        if hasattr(obj, "deleted_at"):
            update_data["deleted_at"] = datetime.now()

        for field in ["actif", "active"]:
            if hasattr(obj, field):
                update_data[field] = False
        try:
            self.repo.update(obj, update_data)
            # On délègue la suite (les cascades) à une méthode spécialisée
            self._after_delete_hook(obj)
        except IntegrityError as exc:
            raise BadRequestException(
                f"Action impossible sur {self.resource_name}"
            ) from exc

    def _after_delete_hook(self, obj: T) -> None:
        """
        Hook destiné à être surchargé dans les services enfants
        pour gérer les cascades spécifiques.
        """
