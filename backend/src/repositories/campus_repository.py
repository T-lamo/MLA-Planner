from typing import Any, List, Optional, cast

from sqlmodel import Session

from models import Campus
from repositories.base_repository import BaseRepository


class CampusRepository(BaseRepository[Campus]):
    def __init__(self, db: Session):
        super().__init__(db, Campus)
        # On définit les relations à charger par défaut pour le campus
        self.relations = [cast(Any, Campus.pays)]

    def get_by_id(
        self, identifiant: str, load_relations: Optional[List[Any]] = None
    ) -> Optional[Campus]:
        rels = load_relations if load_relations is not None else self.relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[Campus]:
        rels = load_relations if load_relations is not None else self.relations
        return super().get_paginated(limit, offset, load_relations=rels)
