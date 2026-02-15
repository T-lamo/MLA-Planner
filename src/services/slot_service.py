# src/services/slot_service.py
from datetime import datetime
from typing import Any, List, Optional

from sqlmodel import Session, select

from core.exceptions.exceptions import BadRequestException, ConflictException
from models import PlanningService, Slot, SlotCreate, SlotRead
from repositories.slot_repository import SlotRepository
from services.assignement_service import AssignmentService

from .base_service import BaseService


class SlotService(BaseService[SlotCreate, SlotRead, Any, Slot]):
    def __init__(self, db: Session):
        super().__init__(SlotRepository(db), "Slot")
        self.db = db

    def _validate_slot_constraints(
        self,
        planning_id: str,
        date_debut: datetime,
        date_fin: datetime,
        exclude_slot_id: Optional[str] = None,
    ):
        """Valide les règles métier : cohérence, bornes activité et collisions."""
        # 1. Cohérence temporelle
        if date_fin <= date_debut:
            raise BadRequestException(
                "La date de fin doit être après la date de début."
            )

        # 2. Vérification des bornes de l'activité liée
        planning = self.db.get(PlanningService, planning_id)
        if not planning or not planning.activite:
            raise BadRequestException("Planning ou activité introuvable.")

        if (
            date_debut < planning.activite.date_debut
            or date_fin > planning.activite.date_fin
        ):
            raise BadRequestException(
                f"Le créneau doit être compris dans l'activité"
                f"({planning.activite.date_debut} - {planning.activite.date_fin})."
            )

        # 3. Vérification de chevauchement (Overlap)
        query = select(Slot).where(
            Slot.planning_id == planning_id,
            Slot.date_debut < date_fin,
            Slot.date_fin > date_debut,
        )
        if exclude_slot_id:
            query = query.where(Slot.id != exclude_slot_id)

        collision = self.db.exec(query).first()
        if collision:
            raise ConflictException(
                f"Collision avec le créneau existant : '{collision.nom_creneau}'"
            )

    def update_slot_secure(self, slot_id: str, data: Any) -> Slot:
        """Met à jour un slot en validant les nouvelles contraintes temporelles."""
        slot = self.get_one(slot_id)

        # Extraction sécurisée des dates
        new_start = getattr(data, "date_debut", None)
        new_end = getattr(data, "date_fin", None)

        if isinstance(data, dict):
            new_start = new_start or data.get("date_debut")
            new_end = new_end or data.get("date_fin")

        new_start = new_start or slot.date_debut
        new_end = new_end or slot.date_fin

        self._validate_slot_constraints(
            slot.planning_id, new_start, new_end, exclude_slot_id=slot.id
        )

        # Conversion du payload en dictionnaire pour le BaseService
        if hasattr(data, "model_dump"):
            update_data = data.model_dump(exclude={"affectations"}, exclude_unset=True)
        else:
            update_data = {k: v for k, v in data.items() if k != "affectations"}

        return self.repo.update(slot, update_data)

    def add_slot_to_planning(self, planning_id: str, data: SlotCreate) -> Slot:
        self._validate_slot_constraints(planning_id, data.date_debut, data.date_fin)
        slot_data = data.model_dump(exclude={"planning_id"})
        new_slot = Slot(**slot_data, planning_id=planning_id)
        return self.repo.create(new_slot)

    def sync_planning_slots(self, planning_id: str, slots_data: List[Any]):
        """Gère le cycle de vie complet (Sync) des slots et de leurs affectations."""
        assignment_svc = AssignmentService(self.db)

        # 1. État actuel
        db_slots = self.db.exec(
            select(Slot).where(Slot.planning_id == planning_id)
        ).all()
        current_map = {s.id: s for s in db_slots}

        payload_ids = {
            getattr(s, "id", None) for s in slots_data if getattr(s, "id", None)
        }

        # 2. DELETE
        for s_id, _slot_obj in current_map.items():
            if s_id not in payload_ids:
                self.delete(s_id)

        # 3. UPSERT
        for s_data in slots_data:
            slot_id = getattr(s_data, "id", None)

            if isinstance(slot_id, str) and slot_id in current_map:
                slot_db = self.update_slot_secure(slot_id, s_data)
            else:
                # Extraction des données pour création
                if hasattr(s_data, "model_dump"):
                    create_dict = s_data.model_dump(
                        exclude={"affectations", "id", "planning_id"}
                    )
                else:
                    create_dict = {
                        k: v
                        for k, v in s_data.items()
                        if k not in ["affectations", "id", "planning_id"]
                    }

                s_create = SlotCreate(**create_dict, planning_id=planning_id)
                slot_db = self.add_slot_to_planning(planning_id, s_create)

            # 4. Cascade vers les affectations (Sécurisé contre AttributeError)
            aff_data = getattr(s_data, "affectations", None)
            if aff_data is None and isinstance(s_data, dict):
                aff_data = s_data.get("affectations", [])

            assignment_svc.sync_assignments(slot_db.id, aff_data or [])
