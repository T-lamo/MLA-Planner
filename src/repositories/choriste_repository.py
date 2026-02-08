# src/repositories/choriste_repository.py
from typing import Any, List, cast

from sqlmodel import Session, select

from models import Choriste, ChoristeVoix
from repositories.base_repository import BaseRepository


class ChoristeRepository(BaseRepository[Choriste]):
    def __init__(self, db: Session):
        super().__init__(db, Choriste)
        # On définit voix_assoc comme relation par défaut
        self.relations = [
            cast(Any, Choriste.voix_assoc),
            # Tu pourrais ajouter cast(Any, Choriste.chantre) si besoin
        ]

    def create_with_voix(self, db_obj: Choriste, voix_in: List[Any]) -> Choriste:
        """Crée un choriste et ses associations de voix de manière atomique."""
        self.db.add(db_obj)
        self.db.flush()  # Récupère l'ID du choriste

        for v in voix_in:
            liaison = ChoristeVoix(
                choriste_id=db_obj.id,
                voix_code=v.voix_code,
                is_principal=v.is_principal,
            )
            self.db.add(liaison)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_voix(self, choriste_id: str, voix_in: List[Any]):
        """Remplace toutes les voix d'un choriste."""
        # 1. Supprimer les anciennes voix
        statement = select(ChoristeVoix).where(ChoristeVoix.choriste_id == choriste_id)
        results = self.db.exec(statement).all()
        for r in results:
            self.db.delete(r)

        # 2. Ajouter les nouvelles
        for v in voix_in:
            new_v = ChoristeVoix(
                choriste_id=choriste_id,
                voix_code=v.voix_code,
                is_principal=v.is_principal,
            )
            self.db.add(new_v)
        self.db.commit()
