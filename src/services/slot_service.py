# src/services/slot_service.py
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from core.exceptions.exceptions import BadRequestException
from models import Slot, SlotCreate, SlotRead  # Supposés créés précédemment
from repositories.slot_repository import SlotRepository

from .base_service import BaseService


class SlotService(BaseService[SlotCreate, SlotRead, Any, Slot]):
    def __init__(self, db: Session):
        super().__init__(SlotRepository(db), "Slot")

    def update_dates(self, slot_id: str, start: datetime, end: datetime):
        slot = self.get_one(slot_id)
        return self.repo.update(slot, {"date_debut": start, "date_fin": end})

    def add_slot_to_planning(self, planning_id: str, data: SlotCreate) -> Slot:
        # 1. Validation de cohérence temporelle
        if data.date_fin <= data.date_debut:
            raise BadRequestException(
                "La date de fin doit être après la date de début."
            )

        # 2. Vérification de chevauchement (Overlap) pour ce planning
        existing_slots = self.repo.db.exec(
            select(Slot).where(
                Slot.planning_id == planning_id,
                Slot.date_debut < data.date_fin,
                Slot.date_fin > data.date_debut,
            )
        ).all()

        if existing_slots:
            raise BadRequestException(
                "Ce créneau chevauche un créneau existant sur ce planning."
            )

        # 3. Création
        new_slot = Slot(**data.model_dump(), planning_id=planning_id)
        return self.repo.create(new_slot)
