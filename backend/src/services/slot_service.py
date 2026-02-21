import logging
from datetime import datetime
from typing import Any, List, Optional

from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import PlanningService, Slot, SlotCreate, SlotRead
from models.membre_model import MemberAgendaEntryRead, MemberAgendaStats
from repositories.slot_repository import SlotRepository
from services.affectation_service import AffectationService
from utils.utils_func import extract_field

from .base_service import BaseService

logger = logging.getLogger(__name__)


class SlotService(BaseService[SlotCreate, SlotRead, Any, Slot]):
    def __init__(self, db: Session):
        super().__init__(SlotRepository(db), "Slot")
        self.db = db
        self.affectation_svc = AffectationService(self.db)

    def _validate_slot_constraints(
        self,
        planning_id: str,
        date_debut: datetime,
        date_fin: datetime,
        exclude_slot_id: Optional[str] = None,
    ):
        """Valide les règles métier : cohérence, bornes activité et collisions."""

        # 1. Vérification chronologique
        if date_fin <= date_debut:
            raise AppException(ErrorRegistry.SLOT_CHRONOLOGY_ERROR)

        # 2. Vérification existence Planning/Activité
        planning = self.db.get(PlanningService, planning_id)
        if not planning or not planning.activite:
            raise AppException(ErrorRegistry.PLANNING_NOT_FOUND)

        # 3. Vérification des bornes de l'activité
        if (
            date_debut < planning.activite.date_debut
            or date_fin > planning.activite.date_fin
        ):
            raise AppException(
                ErrorRegistry.SLOT_OUT_OF_BOUNDS,
                debut=planning.activite.date_debut,
                fin=planning.activite.date_fin,
            )

        # 4. Détection de collisions
        query = select(Slot).where(
            Slot.planning_id == planning_id,
            Slot.date_debut < date_fin,
            Slot.date_fin > date_debut,
        )
        if exclude_slot_id:
            query = query.where(Slot.id != exclude_slot_id)

        collision = self.db.exec(query).first()
        if collision:
            raise AppException(ErrorRegistry.SLOT_COLLISION, nom=collision.nom_creneau)

    def update_slot_secure(self, slot_id: str, data: Any) -> Slot:
        """Met à jour un slot en validant les nouvelles contraintes temporelles."""
        slot = self.get_one(slot_id)

        new_start = extract_field(data, "date_debut") or slot.date_debut
        new_end = extract_field(data, "date_fin") or slot.date_fin

        self._validate_slot_constraints(
            slot.planning_id, new_start, new_end, exclude_slot_id=slot.id
        )

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

        db_slots = self.db.exec(
            select(Slot).where(Slot.planning_id == planning_id)
        ).all()
        current_map = {str(s.id): s for s in db_slots}

        active_payload_ids = []
        for s_data in slots_data:
            p_id = extract_field(s_data, "id")
            if p_id:
                active_payload_ids.append(str(p_id))

        for s_id, slot_obj in current_map.items():
            if s_id not in active_payload_ids:
                self.affectation_svc.delete_by_slot(s_id)
                self.db.delete(slot_obj)

        self.db.flush()

        for s_data in slots_data:
            s_id = extract_field(s_data, "id")

            if s_id and str(s_id) in current_map:
                slot_db = self.update_slot_secure(str(s_id), s_data)
            else:
                s_create = SlotCreate(
                    **self._prepare_slot_create_dict(s_data), planning_id=planning_id
                )
                slot_db = self.add_slot_to_planning(planning_id, s_create)

            self.affectation_svc.sync_affectations(
                slot_db.id, extract_field(s_data, "affectations", [])
            )

    def delete_by_planning(self, planning_id: str) -> None:
        """Supprime tous les créneaux et leurs affectations pour un planning donné."""
        db_slots = self.db.exec(
            select(Slot).where(Slot.planning_id == planning_id)
        ).all()

        for slot in db_slots:
            self.affectation_svc.delete_by_slot(slot.id)
            self.db.delete(slot)

        self.db.flush()

    def get_slots_metrics(self, slots: List[Slot]) -> tuple[int, int]:
        """
        Calcule les métriques globales pour une liste de slots.

        Args:
            slots: Liste des objets Slot à analyser.

        Returns:
            tuple: (nombre_total_slots, nombre_slots_remplis)
        """
        total = len(slots)

        # On utilise l'AffectationService pour vérifier la condition métier "rempli"
        filled = sum(1 for s in slots if self.affectation_svc.is_slot_filled(s))

        return total, filled

    def get_agenda_statistics(self, affectations: list) -> MemberAgendaStats:
        # Cascade : Slot appelle Affectation
        raw_stats = self.affectation_svc.get_stats_from_list(affectations)
        return MemberAgendaStats(
            total_engagements=raw_stats["total"],
            confirmed_rate=raw_stats["rate"],
            roles_distribution=raw_stats["roles"],
        )

    def map_affectations_to_entries(
        self, affectations: list
    ) -> List[MemberAgendaEntryRead]:
        entries = []
        for aff in affectations:
            # On prépare un dictionnaire compatible avec le DTO
            # pour utiliser model_validate
            payload = {
                "affectation_id": str(aff.id),
                "statut_affectation_code": aff.statut_affectation_code,
                "role_code": aff.role_code,
                "nom_creneau": aff.slot.nom_creneau,
                "date_debut": aff.slot.date_debut,
                "date_fin": aff.slot.date_fin,
                "activite_nom": aff.slot.planning.activite.nom
                or aff.slot.planning.activite.type,
                "activite_type": aff.slot.planning.activite.type,
                "lieu": aff.slot.planning.activite.lieu,
                "campus_nom": (
                    aff.slot.planning.activite.campus.nom
                    if aff.slot.planning.activite.campus
                    else "N/A"
                ),
            }
            entries.append(MemberAgendaEntryRead.model_validate(payload))
        return entries
