from core.exceptions import BadRequestException, NotFoundException
from models import Pole, PoleCreate, PoleRead, PoleUpdate
from repositories.ministere_repository import (
    MinistereRepository,  # À adapter selon ton projet
)
from repositories.pole_repository import PoleRepository
from services.base_service import BaseService
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


class PoleService(BaseService[PoleCreate, PoleRead, PoleUpdate, Pole]):
    def __init__(self, db: Session):
        super().__init__(repo=PoleRepository(db), resource_name="Pole")
        self.ministere_repo = MinistereRepository(db)

    def create(self, data: PoleCreate) -> Pole:
        # Vérification métier : le ministère doit exister
        if not self.ministere_repo.get_by_id(data.ministere_id):
            raise NotFoundException(f"Ministère {data.ministere_id} introuvable.")

        pole = Pole(**data.model_dump())
        try:
            return self.repo.create(pole)
        except IntegrityError as exc:
            raise BadRequestException("Un pôle avec ce nom existe déjà.") from exc

    def update(self, identifiant: str, data: PoleUpdate) -> Pole:
        pole_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        if "ministere_id" in update_data:
            if not self.ministere_repo.get_by_id(update_data["ministere_id"]):
                raise NotFoundException("Ministère invalide.")

        return self.repo.update(pole_db, update_data)
