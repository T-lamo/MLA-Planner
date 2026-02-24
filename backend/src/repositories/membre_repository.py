from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from models import Membre

# Importation des tables de liaison si nécessaire pour des requêtes complexes
from models.schema_db_model import (
    MembreRole,
)
from repositories.base_repository import BaseRepository


class MembreRepository(BaseRepository[Membre]):
    def __init__(self, db: Session):
        super().__init__(db, Membre)
        # MISE À JOUR : On charge les nouvelles relations PLURIELLES (N:N)
        self.default_relations = [
            cast(Any, Membre.campuses),  # Nouveau : N:N
            cast(Any, Membre.ministeres),  # Nouveau : N:N
            cast(Any, Membre.poles),  # Nouveau : N:N
            cast(Any, Membre.utilisateur),
            cast(Any, Membre.roles_assoc),
        ]

    def get_by_id(
        self, identifiant: Any, load_relations: Optional[List[Any]] = None
    ) -> Optional[Membre]:
        """Surcharge pour inclure les relations par défaut (N:N chargées)."""
        rels = load_relations if load_relations is not None else self.default_relations
        return super().get_by_id(identifiant, load_relations=rels)

    def get_membre_with_roles(self, membre_id: str) -> Optional[Membre]:
        """Récupère un membre avec ses rôles et ses rattachés (N:N)."""

        statement = (
            select(Membre)
            .where(Membre.id == membre_id)
            .options(
                # Chargement des rôles et de la définition du rôle
                selectinload(cast(Any, Membre.roles_assoc)).selectinload(
                    cast(Any, MembreRole.role)
                ),
                # Chargement des rattachés N:N pour éviter le LazyLoading plus tard
                selectinload(cast(Any, Membre.campuses)),
                selectinload(cast(Any, Membre.ministeres)),
                selectinload(cast(Any, Membre.poles)),
            )
        )

        result = self.db.exec(statement).unique().first()
        if result:
            # Refresh optionnel mais recommandé après un changement de schéma
            self.db.refresh(result)
        return result

    def get_all_with_relations(self) -> List[Membre]:
        """Récupère tous les membres avec leurs campus/ministères/pôles."""
        statement = select(Membre).options(
            selectinload(cast(Any, Membre.campuses)),
            selectinload(cast(Any, Membre.ministeres)),
            selectinload(cast(Any, Membre.poles)),
        )
        return list(self.db.exec(statement).unique().all())
