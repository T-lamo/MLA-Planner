from typing import Any, Optional

from models import MembreRole
from sqlmodel import Session

from .base_repository import BaseRepository


class MembreRoleRepository(BaseRepository[MembreRole]):
    def __init__(self, db: Session):
        super().__init__(db, MembreRole)

    def get_by_id(self, identifiant: Any, load_relations=None) -> Optional[MembreRole]:
        """
        Surcharge pour PK Composite.
        identifiant peut être un tuple (membre_id, role_code).
        """
        if isinstance(identifiant, tuple):
            m_id, r_code = identifiant
        else:
            # Sécurité pour les appels via router (string formatée)
            m_id, r_code = identifiant.split(":")

        statement = self._get_base_query(load_relations).where(
            MembreRole.membre_id == m_id, MembreRole.role_code == r_code.strip().upper()
        )
        return self.db.exec(statement).unique().first()
