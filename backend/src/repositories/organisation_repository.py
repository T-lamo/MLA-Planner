# src/repositories/organisation_repository.py
from typing import Any, List, Optional, cast

from sqlmodel import Session, select

from models import Organisation
from repositories.base_repository import BaseRepository


class OrganisationRepository(BaseRepository[Organisation]):
    def __init__(self, db: Session):
        super().__init__(db, Organisation)
        self.relations = [cast(Any, Organisation.children)]

    # Correction de la signature : on ajoute load_relations
    def get_by_id(
        self, identifiant: str, load_relations: Optional[List[Any]] = None
    ) -> Optional[Organisation]:
        # On utilise les relations passées, sinon celles par défaut de la classe
        rels = load_relations if load_relations is not None else self.relations
        return super().get_by_id(identifiant, load_relations=rels)

    # Correction de la signature : on ajoute load_relations
    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[Organisation]:
        rels = load_relations if load_relations is not None else self.relations
        return super().get_paginated(limit, offset, load_relations=rels)

    def get_by_nom(self, nom: str) -> Optional[Organisation]:
        return self.db.exec(select(self.model).where(self.model.nom == nom)).first()
