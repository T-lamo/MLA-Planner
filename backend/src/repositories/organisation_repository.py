# src/repositories/organisation_repository.py
from typing import Any, List, Optional, cast

from models import OrganisationICC
from repositories.base_repository import BaseRepository
from sqlmodel import Session, select


class OrganisationRepository(BaseRepository[OrganisationICC]):
    def __init__(self, db: Session):
        super().__init__(db, OrganisationICC)
        self.relations = [cast(Any, OrganisationICC.pays)]

    # Correction de la signature : on ajoute load_relations
    def get_by_id(
        self, identifiant: str, load_relations: Optional[List[Any]] = None
    ) -> Optional[OrganisationICC]:
        # On utilise les relations passées, sinon celles par défaut de la classe
        rels = load_relations if load_relations is not None else self.relations
        return super().get_by_id(identifiant, load_relations=rels)

    # Correction de la signature : on ajoute load_relations
    def get_paginated(
        self, limit: int, offset: int, load_relations: Optional[List[Any]] = None
    ) -> List[OrganisationICC]:
        rels = load_relations if load_relations is not None else self.relations
        return super().get_paginated(limit, offset, load_relations=rels)

    def get_by_nom(self, nom: str) -> Optional[OrganisationICC]:
        return self.db.exec(select(self.model).where(self.model.nom == nom)).first()
