from typing import Optional

from sqlmodel import Session

from models import CategorieRole
from repositories.base_repository import BaseRepository


class CategorieRoleRepository(BaseRepository[CategorieRole]):
    def __init__(self, db: Session):
        super().__init__(db, CategorieRole)

    def get_by_id(
        self, identifiant: str, load_relations=None
    ) -> Optional[CategorieRole]:
        """Surcharge car l'identifiant est 'code' et non 'id'."""
        statement = self._get_base_query(load_relations).where(
            CategorieRole.code == identifiant.upper().strip()
        )
        return self.db.exec(statement).unique().first()
