from typing import Any, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from models import Equipe
from models.schema_db_model import EquipeMembre
from repositories.base_repository import BaseRepository


class EquipeRepository(BaseRepository[Equipe]):
    def __init__(self, db: Session):
        super().__init__(db, Equipe)
        # On définit le chargement profond : Equipe -> Table Liaison -> Membre
        self.default_relations = [
            cast(Any, Equipe.membres_assoc),
            # selectinload(cast(Any, Equipe.membres_assoc)).selectinload(
            #     cast(Any, EquipeMembre.membre)
            # )
        ]

    def get_with_members(self, equipe_id: str) -> Optional[Equipe]:
        """
        Charge une équipe et ses membres associés (via la table de liaison)
        en une seule requête optimisée.
        """
        # Construction de la requête avec chargement eager (selectinload)
        # On charge Equipe -> membres_assoc (liaison) -> membre (l'entité membre)
        statement = (
            select(Equipe)
            .where(Equipe.id == equipe_id)
            .options(
                selectinload(cast(Any, Equipe.membres_assoc)).selectinload(
                    cast(Any, EquipeMembre.membre)
                )
            )
        )

        # .unique() est obligatoire avec selectinload sur des relations many-to-many
        # .first() retourne le premier résultat ou None
        result = self.db.exec(statement).unique().first()

        return result
