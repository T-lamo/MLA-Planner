# src/repositories/pays_repository.py
from typing import Any, List, Optional, cast

from models import Pays
from repositories.base_repository import BaseRepository
from sqlmodel import Session


class PaysRepository(BaseRepository[Pays]):
    def __init__(self, db: Session):
        super().__init__(db, Pays)
        self.relations = [cast(Any, Pays.organisation)]

    # Ajout de load_relations=None pour matcher la signature parente
    def get_by_id(
        self, identifiant: str, load_relations: Optional[List[Any]] = None
    ) -> Optional[Pays]:
        # Si aucune relation n'est passée, on utilise les relations par défaut
        rels = load_relations if load_relations is not None else self.relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[Pays]:
        rels = load_relations if load_relations is not None else self.relations
        return super().get_paginated(limit, offset, load_relations=rels)
