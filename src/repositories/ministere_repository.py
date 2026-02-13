from typing import Any, List, Optional, cast

from sqlmodel import Session

from models import Ministere
from repositories.base_repository import BaseRepository


class MinistereRepository(BaseRepository[Ministere]):
    def __init__(self, db: Session):
        super().__init__(db, Ministere)
        # On définit les relations à charger par défaut pour le ministère
        # cast(Any, ...) aide à éviter les erreurs de type
        # SQLModel/Mypy sur les attributs de relation
        self.relations = [
            cast(Any, Ministere.poles),
            cast(Any, Ministere.membres),
            # cast(Any, Ministere.equipes),
            # cast(Any, Ministere.campus),
        ]

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Ministere]:
        """Récupère un ministère avec ses relations par défaut."""
        rels = load_relations if load_relations is not None else self.relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[Ministere]:
        """Récupère la liste paginée avec les relations chargées."""
        rels = load_relations if load_relations is not None else self.relations
        return super().get_paginated(limit, offset, load_relations=rels)
