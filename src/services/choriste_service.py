# src/services/choriste_service.py
from sqlmodel import Session

from models import Choriste, ChoristeCreate, ChoristeRead, ChoristeUpdate
from repositories.choriste_repository import ChoristeRepository
from services.base_service import BaseService


class ChoristeService(
    BaseService[ChoristeCreate, ChoristeRead, ChoristeUpdate, Choriste]
):
    def __init__(self, db: Session):
        super().__init__(repo=ChoristeRepository(db), resource_name="Choriste")

    def create(self, data: ChoristeCreate) -> Choriste:
        db_obj = Choriste(chantre_id=data.chantre_id)
        return self.repo.create_with_voix(db_obj, data.voix_assoc)

    def update(self, identifiant: str, data: ChoristeUpdate) -> Choriste:
        db_obj = self.get_one(identifiant)
        update_dict = data.model_dump(exclude_unset=True)

        if "voix_assoc" in update_dict:
            self.repo.update_voix(identifiant, data.voix_assoc)
            del update_dict["voix_assoc"]

        return self.repo.update(db_obj, update_dict)
