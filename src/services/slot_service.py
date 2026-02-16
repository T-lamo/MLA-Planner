# src/services/slot_service.py
from datetime import datetime
from typing import Any, List, Optional

from sqlmodel import Session, select

from core.exceptions.exceptions import BadRequestException, ConflictException
from models import PlanningService, Slot, SlotCreate, SlotRead
from repositories.slot_repository import SlotRepository
from services.assignement_service import AssignmentService

# --- IMPORTATION DE LA FONCTION UTILITAIRE ---
from utils.utils_func import extract_field

from .base_service import BaseService

# ----------------------------------------------


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
        if date_fin <= date_debut:
            raise BadRequestException(
                "La date de fin doit être après la date de début."
            )

        planning = self.db.get(PlanningService, planning_id)
        if not planning or not planning.activite:
            raise BadRequestException("Planning ou activité introuvable.")

        if (
            date_debut < planning.activite.date_debut
            or date_fin > planning.activite.date_fin
        ):
            raise BadRequestException(
                f"Le créneau doit être compris dans l'activité "
                f"({planning.activite.date_debut} - {planning.activite.date_fin})."
            )

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

        # Utilisation de extract_field pour les dates
        new_start = extract_field(data, "date_debut") or slot.date_debut
        new_end = extract_field(data, "date_fin") or slot.date_fin

        self._validate_slot_constraints(
            slot.planning_id, new_start, new_end, exclude_slot_id=slot.id
        )

        # Préparation des données pour le repository
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

    def _prepare_slot_create_dict(self, s_data: Any) -> dict:
        """Extrait les données pour la création d'un slot en excluant les relations."""
        exclude_fields = {"affectations", "id", "planning_id"}
        if hasattr(s_data, "model_dump"):
            return s_data.model_dump(exclude=exclude_fields)

        return {k: v for k, v in s_data.items() if k not in exclude_fields}

    def sync_planning_slots(self, planning_id: str, slots_data: List[Any]):
        """Gère le cycle de vie complet (Sync) des slots et de leurs affectations."""
        assignment_svc = AssignmentService(self.db)

        # 1. Chargement et Delta
        db_slots = self.db.exec(
            select(Slot).where(Slot.planning_id == planning_id)
        ).all()
        current_map = {str(s.id): s for s in db_slots}

        # 2. DELETE : Suppression des slots absents
        active_payload_ids = []
        for s_data in slots_data:
            p_id = extract_field(s_data, "id")
            if p_id:
                active_payload_ids.append(str(p_id))

        for s_id, slot_obj in current_map.items():
            if s_id not in active_payload_ids:
                assignment_svc.delete_by_slot(s_id)
                self.db.delete(slot_obj)

        self.db.flush()

        # 3. UPSERT
        for s_data in slots_data:
            s_id = extract_field(s_data, "id")

            # On traite directement sans créer trop de variables intermédiaires
            if s_id and str(s_id) in current_map:
                slot_db = self.update_slot_secure(str(s_id), s_data)
            else:
                s_create = SlotCreate(
                    **self._prepare_slot_create_dict(s_data), planning_id=planning_id
                )
                slot_db = self.add_slot_to_planning(planning_id, s_create)

            assignment_svc.sync_assignments(
                slot_db.id, extract_field(s_data, "affectations", [])
            )

    def delete_by_planning(self, planning_id: str) -> None:
        """Supprime tous les créneaux et leurs affectations pour un planning donné."""
        assignment_svc = AssignmentService(self.db)
        db_slots = self.db.exec(
            select(Slot).where(Slot.planning_id == planning_id)
        ).all()

        for slot in db_slots:
            assignment_svc.delete_by_slot(slot.id)
            self.db.delete(slot)

        self.db.flush()
