from sqlmodel import Session

from models import Slot
from repositories.base_repository import BaseRepository


class SlotRepository(BaseRepository[Slot]):
    def __init__(self, db: Session):
        super().__init__(db, Slot)
