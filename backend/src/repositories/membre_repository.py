from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, distinct, func, select

from models import Membre
from models.schema_db_model import (
    Campus,
    MembreRole,
)
from repositories.base_repository import BaseRepository


class MembreRepository(BaseRepository[Membre]):
    def __init__(self, db: Session):
        super().__init__(db, Membre)
        self.default_relations = [
            cast(Any, Membre.campuses),
            cast(Any, Membre.ministeres),
            cast(Any, Membre.poles),
            cast(Any, Membre.utilisateur),
            cast(Any, Membre.roles_assoc),
        ]

    def get_paginated(
        self,
        limit: int,
        offset: int,
        load_relations: Optional[List[Any]] = None,
        campus_id: Optional[str] = None,  # Ajouté en paramètre nommé optionnel
    ) -> List[Membre]:
        """
        Version compatible LSP. On utilise load_relations de la base
        et on ajoute campus_id.
        """
        # Utilisation de col() pour rassurer mypy sur l'attribut SQL
        statement = select(Membre).where(col(Membre.deleted_at).is_(None))

        if campus_id:
            # On cast Membre.campuses en Any pour mypy lors du join
            statement = statement.join(cast(Any, Membre.campuses)).where(
                Campus.id == campus_id
            )

        rels = (
            load_relations
            if load_relations is not None
            else [
                cast(Any, Membre.utilisateur),
                cast(Any, Membre.campuses),
                cast(Any, Membre.ministeres),
                cast(Any, Membre.poles),
            ]
        )

        statement = statement.options(*[selectinload(r) for r in rels])
        statement = statement.limit(limit).offset(offset).distinct()

        return list(self.db.exec(statement).unique().all())

    def count(self, campus_id: Optional[str] = None) -> int:
        """Compte total de membres avec filtre campus."""
        # pylint: disable=not-callable
        statement = select(func.count(distinct(Membre.id))).where(
            col(Membre.deleted_at).is_(None)
        )

        if campus_id:
            statement = statement.join(cast(Any, Membre.campuses)).where(
                Campus.id == campus_id
            )

        return self.db.exec(statement).one()

    def list_all(
        self,
        load_relations: Optional[List[Any]] = None,
        campus_id: Optional[str] = None,
    ) -> List[Membre]:
        """Récupère tous les membres actifs avec compatibilité LSP."""
        statement = select(Membre).where(col(Membre.deleted_at) == None)  # noqa: E711

        if campus_id:
            statement = statement.join(cast(Any, Membre.campuses)).where(
                Campus.id == campus_id
            )

        rels = (
            load_relations
            if load_relations is not None
            else [
                cast(Any, Membre.campuses),
                cast(Any, Membre.ministeres),
                cast(Any, Membre.poles),
            ]
        )

        statement = statement.options(*[selectinload(r) for r in rels]).distinct()

        return list(self.db.exec(statement).unique().all())

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Membre]:
        """Surcharge pour inclure les relations par défaut."""
        rels = load_relations if load_relations is not None else self.default_relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_membre_with_roles(self, membre_id: str) -> Optional[Membre]:
        """Récupère un membre avec ses rôles et rattachés."""
        statement = (
            select(Membre)
            .where(Membre.id == membre_id)
            .options(
                selectinload(cast(Any, Membre.roles_assoc)).selectinload(
                    cast(Any, MembreRole.role)
                ),
                selectinload(cast(Any, Membre.campuses)),
                selectinload(cast(Any, Membre.ministeres)),
                selectinload(cast(Any, Membre.poles)),
            )
        )

        result = self.db.exec(statement).unique().first()
        if result:
            self.db.refresh(result)
        return result
