from models import Activite
from repositories.base_repository import BaseRepository
from sqlmodel import Session


class ActiviteRepository(BaseRepository[Activite]):
    def __init__(self, db: Session):
        super().__init__(db, Activite)
