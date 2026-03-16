# src/repositories/indisponibilite_repository.py
from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from models.schema_db_model import (
    Indisponibilite,
    MembreCampusLink,
)
from repositories.base_repository import BaseRepository


class IndisponibiliteRepository(BaseRepository[Indisponibilite]):
    """Repository pour les indisponibilités des membres."""

    def __init__(self, db: Session):
        super().__init__(db, Indisponibilite)

    def _eager_stmt(self, stmt: Any) -> Any:
        """Ajoute les options d'eager loading."""
        return stmt.options(
            selectinload(cast(Any, Indisponibilite.membre)),
            selectinload(cast(Any, Indisponibilite.ministere)),
        )

    def get_by_membre(self, membre_id: str) -> List[Indisponibilite]:
        """Indisponibilités d'un membre (toutes)."""
        stmt = self._eager_stmt(
            select(Indisponibilite).where(Indisponibilite.membre_id == membre_id)
        )
        return list(self.db.exec(stmt).all())  # type: ignore[arg-type]

    def get_by_ministere(self, ministere_id: str) -> List[Indisponibilite]:
        """Indisponibilités liées à un ministère précis."""
        stmt = self._eager_stmt(
            select(Indisponibilite).where(Indisponibilite.ministere_id == ministere_id)
        )
        return list(self.db.exec(stmt).all())  # type: ignore[arg-type]

    def get_by_campus(self, campus_id: str) -> List[Indisponibilite]:
        """Toutes les indisponibilités des membres d'un campus."""
        stmt = self._eager_stmt(
            select(Indisponibilite)
            .join(
                MembreCampusLink,
                col(MembreCampusLink.membre_id) == col(Indisponibilite.membre_id),
            )
            .where(MembreCampusLink.campus_id == campus_id)
        )
        return list(self.db.exec(stmt).all())  # type: ignore[arg-type]

    def get_by_membre_and_ministere(
        self,
        membre_id: str,
        ministere_id: Optional[str],
    ) -> List[Indisponibilite]:
        """Indisponibilités d'un membre pour un ministère (ou globales)."""
        stmt = self._eager_stmt(
            select(Indisponibilite).where(
                Indisponibilite.membre_id == membre_id,
                Indisponibilite.ministere_id == ministere_id,
            )
        )
        return list(self.db.exec(stmt).all())  # type: ignore[arg-type]

    def get_pending_validation(self, campus_id: str) -> List[Indisponibilite]:
        """Indisponibilités non validées d'un campus."""
        stmt = self._eager_stmt(
            select(Indisponibilite)
            .join(
                MembreCampusLink,
                col(MembreCampusLink.membre_id) == col(Indisponibilite.membre_id),
            )
            .where(
                MembreCampusLink.campus_id == campus_id,
                col(Indisponibilite.validee) == False,  # noqa: E712
            )
        )
        return list(self.db.exec(stmt).all())  # type: ignore[arg-type]

    def get_overlapping(
        self,
        membre_id: str,
        date_debut: str,
        date_fin: str,
        ministere_id: Optional[str],
        *,
        exclude_id: Optional[str] = None,
    ) -> List[Indisponibilite]:
        """Indisponibilités qui chevauchent une période pour un membre."""
        stmt = select(Indisponibilite).where(
            Indisponibilite.membre_id == membre_id,
            Indisponibilite.ministere_id == ministere_id,
            col(Indisponibilite.date_debut) <= date_fin,
            col(Indisponibilite.date_fin) >= date_debut,
        )
        if exclude_id:
            stmt = stmt.where(Indisponibilite.id != exclude_id)
        return list(self.db.exec(stmt).all())
