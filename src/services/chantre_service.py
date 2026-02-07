from sqlmodel import Session

from models import Chantre, ChantreCreate, ChantreRead, ChantreUpdate
from repositories.chantre_repository import ChantreRepository

from .base_service import BaseService


class ChantreService(BaseService[ChantreCreate, ChantreRead, ChantreUpdate, Chantre]):
    def __init__(self, db: Session):
        super().__init__(repo=ChantreRepository(db), resource_name="Chantre")

    def create(self, data: ChantreCreate) -> Chantre:
        db_obj = Chantre.model_validate(data)
        return self.repo.create(db_obj)

    def update(self, identifiant: str, data: ChantreUpdate) -> Chantre:
        db_obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)
        return self.repo.update(db_obj, update_data)
