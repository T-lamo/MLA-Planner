from typing import Any, List, Optional, cast

from sqlmodel import Session

from models import Chantre

from .base_repository import BaseRepository


class ChantreRepository(BaseRepository[Chantre]):
    def __init__(self, db: Session):
        super().__init__(db, Chantre)

    def _get_chantre_relations(self):
        """Liste des relations nécessaires pour les schémas Read."""
        return [
            # Chantre.choristes,
            # Chantre.musiciens,
            # Chantre.affectations,
            # Chantre.indisponibilites,
        ]

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Chantre]:
        # On force le chargement des relations pour les counts de ChantreRead
        rels = load_relations or self._get_chantre_relations()
        statement = self._get_base_query(rels).where(
            cast(Any, self.model).id == identifiant
        )
        return self.db.exec(statement).unique().first()
