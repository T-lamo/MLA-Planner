from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions import BadRequestException, ConflictException
from models import Activite, ActiviteCreate, ActiviteRead, ActiviteUpdate
from repositories.activite_repository import ActiviteRepository
from services.base_service import BaseService


class ActiviteService(
    BaseService[ActiviteCreate, ActiviteRead, ActiviteUpdate, Activite]
):
    def __init__(self, db: Session):
        self.repo = ActiviteRepository(db)
        super().__init__(self.repo, resource_name="Activité")

    def create(self, data: ActiviteCreate) -> Activite:
        try:
            activite_obj = Activite.model_validate(data)
            return self.repo.create(activite_obj)
        except IntegrityError as e:
            # Gestion des violations de clés étrangères (campus_id, etc.)
            raise BadRequestException(
                "Données de référence (Campus/Ministère) invalides."
            ) from e

    def update(self, identifiant: str, data: ActiviteUpdate) -> Activite:
        db_obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)
        try:
            return self.repo.update(db_obj, update_data)
        except IntegrityError as e:
            raise ConflictException(
                "Erreur de contrainte lors de la mise à jour."
            ) from e

    def hard_delete(self, activite_id: str) -> None:
        """Supprime physiquement l'activité de la base de données."""
        activite = self.get_one(activite_id)
        self.repo.delete(activite)
