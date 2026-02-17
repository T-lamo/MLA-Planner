from models import Slot
from repositories.base_repository import BaseRepository
from sqlmodel import Session


class SlotRepository(BaseRepository[Slot]):
    def __init__(self, db: Session):
        super().__init__(db, Slot)
