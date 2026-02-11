# src/repositories/base_repository.py
from typing import Any, Generic, List, Optional, Type, TypeVar, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, func, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def _get_base_query(self, load_relations: Optional[List[Any]] = None):
        """Construit la requête de base avec ou sans relations."""
        statement = select(self.model)
        # Filtre global pour exclure les soft-deleted des résultats API
        if hasattr(self.model, "deleted_at"):
            statement = statement.where(cast(Any, self.model).deleted_at.is_(None))
        if load_relations:
            for rel in load_relations:
                statement = statement.options(selectinload(rel))
        return statement

    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[T]:
        # On cast le modèle en Any pour accéder à l'attribut .id sans erreur Mypy
        # SQLModel utilise des métaclasses, ce qui rend l'accès
        # direct difficile pour le linting statique
        model_id = cast(Any, self.model).id
        statement = self._get_base_query(load_relations).where(
            model_id == str(identifiant)
        )
        return self.db.exec(statement).unique().first()

    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[T]:
        statement = self._get_base_query(load_relations).offset(offset).limit(limit)
        return list(self.db.exec(statement).unique().all())

    def list_all(self, load_relations: Optional[List[Any]] = None) -> List[T]:
        statement = self._get_base_query(load_relations)
        return list(self.db.exec(statement).unique().all())

    def count(self) -> int:
        # pylint: disable=not-callable
        return self.db.exec(select(func.count()).select_from(self.model)).one()

    def update(self, db_obj: T, update_data: dict) -> T:
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: T) -> None:
        self.db.delete(db_obj)
        self.db.commit()
