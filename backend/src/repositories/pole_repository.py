from models import Pole
from sqlmodel import Session

from .base_repository import BaseRepository


class PoleRepository(BaseRepository[Pole]):
    def __init__(self, db: Session):
        super().__init__(db, Pole)
