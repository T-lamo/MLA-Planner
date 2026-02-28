from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

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

    def get_with_details(self, campus_id: str) -> Optional[Campus]:
        """
        Récupère un campus avec ses membres et ministères en une seule étape
        via Eager Loading (selectinload).
        """
        statement = (
            select(Campus)
            .where(Campus.id == campus_id)
            .options(
                # On cast l'attribut de relation pour que selectinload l'accepte
                selectinload(cast(Any, Campus.ministeres)),
                selectinload(cast(Any, Campus.membres)),
            )
        )
        return self.db.exec(statement).first()
