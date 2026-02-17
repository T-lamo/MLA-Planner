from typing import Any, List, Optional, cast

from models import Membre
from models.schema_db_model import MembreRole
from repositories.base_repository import BaseRepository
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


class MembreRepository(BaseRepository[Membre]):
    def __init__(self, db: Session):
        super().__init__(db, Membre)
        # On définit les relations par défaut à charger pour ce repository métier
        # L'ajout de Membre.utilisateur est CRUCIAL
        # pour le test de sécurité du schéma Read
        self.default_relations = [
            cast(Any, Membre.ministere),
            cast(Any, Membre.pole),
            cast(Any, Membre.utilisateur),
            cast(Any, Membre.roles_assoc),
        ]

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Membre]:
        """Surcharge pour inclure les relations par défaut si aucune n'est spécifiée."""
        rels = load_relations if load_relations is not None else self.default_relations
        return super().get_by_id(identifiant, load_relations=rels)

    # --- MÉTHODE CORRIGÉE POUR MYPY ---
    def get_membre_with_roles(self, membre_id: str) -> Optional[Membre]:
        """Récupère un membre avec ses rôles chargés en optimisant les requêtes."""

        # On force Mypy à comprendre que ce sont des relations SQLAlchemy
        statement = (
            select(Membre)
            .where(Membre.id == membre_id)
            .options(
                selectinload(cast(Any, Membre.roles_assoc)).selectinload(
                    cast(Any, MembreRole.role)
                )
            )
        )

        # unique() est requis lors de l'utilisation de chargements de relations
        # pour garantir l'unicité des objets retournés par le résultat.
        result = self.db.exec(statement).unique().first()
        if result:
            self.db.refresh(result)
        return result
