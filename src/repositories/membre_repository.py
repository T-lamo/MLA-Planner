from typing import Any, List, Optional, cast

from sqlmodel import Session

from models import Membre
from repositories.base_repository import BaseRepository


class MembreRepository(BaseRepository[Membre]):
    def __init__(self, db: Session):
        super().__init__(db, Membre)
        # On définit les relations par défaut à charger pour ce repository métier
        # L'ajout de Membre.utilisateur est CRUCIAL
        # pour le test de sécurité du schéma Read
        self.default_relations = [
            cast(Any, Membre.ministere),
            cast(Any, Membre.pole),
            cast(Any, Membre.utilisateur),
        ]

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Membre]:
        """Surcharge pour inclure les relations par défaut si aucune n'est spécifiée."""
        rels = load_relations if load_relations is not None else self.default_relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[Membre]:
        """Surcharge pour que la liste paginée contienne aussi les relations."""
        rels = load_relations if load_relations is not None else self.default_relations
        return super().get_paginated(limit, offset, load_relations=rels)
