from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from models import CategorieRole, RoleCompetence
from models.schema_db_model import MinistereRoleConfig

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

    def get_all_with_categories(self) -> List[RoleCompetence]:
        """Récupère tous les rôles avec leurs catégories, triés."""
        statement = (
            select(RoleCompetence)
            .join(cast(Any, RoleCompetence.categorie))
            .options(selectinload(cast(Any, RoleCompetence.categorie)))
            .order_by(CategorieRole.libelle, RoleCompetence.libelle)
        )
        return list(self.db.exec(statement).all())

    def get_all_with_categories_for_ministere(
        self, ministere_id: str
    ) -> List[RoleCompetence]:
        """Rôles actifs d'un ministère (via MinistereRoleConfig), triés."""
        statement = (
            select(RoleCompetence)
            .join(
                MinistereRoleConfig,
                col(MinistereRoleConfig.role_code) == col(RoleCompetence.code),
            )
            .join(cast(Any, RoleCompetence.categorie))
            .where(MinistereRoleConfig.ministere_id == ministere_id)
            .options(selectinload(cast(Any, RoleCompetence.categorie)))
            .order_by(CategorieRole.libelle, RoleCompetence.libelle)
        )
        return list(self.db.exec(statement).all())
