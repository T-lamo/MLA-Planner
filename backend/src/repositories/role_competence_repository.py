from typing import Optional

from models import RoleCompetence
from sqlmodel import Session

from .base_repository import BaseRepository


class RoleCompetenceRepository(BaseRepository[RoleCompetence]):
    def __init__(self, db: Session):
        super().__init__(db, RoleCompetence)

    def get_by_id(
        self, identifiant: str, load_relations=None
    ) -> Optional[RoleCompetence]:
        """Surcharge pour utiliser 'code' comme PK naturelle."""
        statement = self._get_base_query(load_relations).where(
            RoleCompetence.code == identifiant.upper().strip()
        )
        return self.db.exec(statement).unique().first()
