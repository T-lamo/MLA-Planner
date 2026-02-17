from core.exceptions import NotFoundException
from models import (
    Indisponibilite,
    IndisponibiliteCreate,
    IndisponibiliteRead,
    IndisponibiliteUpdate,
    Membre,
)
from repositories.base_repository import BaseRepository
from services.base_service import BaseService
from sqlmodel import Session


class IndisponibiliteRepository(BaseRepository[Indisponibilite]):
    def __init__(self, db: Session):
        super().__init__(db, Indisponibilite)


class IndisponibiliteService(
    BaseService[
        IndisponibiliteCreate,
        IndisponibiliteRead,
        IndisponibiliteUpdate,
        Indisponibilite,
    ]
):
    def __init__(self, db: Session):
        super().__init__(
            repo=IndisponibiliteRepository(db), resource_name="Indisponibilite"
        )
        self.db = db

    def create(self, data: IndisponibiliteCreate) -> Indisponibilite:
        # Sécurité : Vérifier que le membre existe avant l'insertion
        # (évite 500 sur FK violation)
        membre = self.db.get(Membre, data.membre_id)
        if not membre:
            raise NotFoundException(f"Membre {data.membre_id} introuvable.")

        return self.repo.create(Indisponibilite(**data.model_dump()))

    def get_by_membre(self, membre_id: str) -> list[Indisponibilite]:
        """Logique métier pour récupérer les indisponibilités d'un membre."""
        # On peut ajouter ici des validations (ex: vérifier si le membre existe)
        return self.repo.get_by_membre(membre_id)
