from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions import BadRequestException, NotFoundException
from models import Campus, CampusCreate, CampusRead, CampusUpdate
from repositories.campus_repository import CampusRepository
from repositories.pays_repository import PaysRepository
from services.base_service import BaseService


class CampusService(BaseService[CampusCreate, CampusRead, CampusUpdate, Campus]):
    def __init__(self, db: Session):
        super().__init__(repo=CampusRepository(db), resource_name="Campus")
        self.pays_repo = PaysRepository(db)

    def create(self, data: CampusCreate) -> Campus:
        # Vérification de l'existence du pays (Contrainte métier)
        if not self.pays_repo.get_by_id(data.pays_id):
            raise NotFoundException(f"Pays avec l'ID {data.pays_id} introuvable.")

        campus = Campus(**data.model_dump())
        try:
            return self.repo.create(campus)
        except IntegrityError as exc:
            raise BadRequestException(
                "Un campus avec ce nom existe peut-être déjà."
            ) from exc

    def update(self, identifiant: str, data: CampusUpdate) -> Campus:
        campus_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Si le pays est modifié, on valide son existence
        if "pays_id" in update_data:
            if not self.pays_repo.get_by_id(update_data["pays_id"]):
                raise NotFoundException("Le nouveau pays spécifié est invalide.")

        try:
            return self.repo.update(campus_db, update_data)
        except IntegrityError as exc:
            raise BadRequestException(
                "Erreur de contrainte lors de la mise à jour."
            ) from exc
