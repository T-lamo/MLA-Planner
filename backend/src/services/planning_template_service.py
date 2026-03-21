"""Service métier pour les templates de planning."""

from typing import List

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models.planning_template_model import (
    PlanningTemplateRead,
    PlanningTemplateRoleRead,
    PlanningTemplateSlotRead,
    PlanningTemplateUpdate,
    SaveAsTemplateRequest,
)
from models.schema_db_model import (
    Activite,
    PlanningService,
    PlanningTemplate,
    PlanningTemplateRole,
    PlanningTemplateSlot,
    Slot,
)
from repositories.planning_template_repository import (
    PlanningTemplateRepository,
)


class PlanningTemplateSvc:
    """Service pour la gestion des templates de planning."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PlanningTemplateRepository(db)

    # ── Lecture ────────────────────────────────────────────────────────

    def get_template(self, template_id: str) -> PlanningTemplateRead:
        """Récupère un template avec ses créneaux et rôles."""
        template = self.repo.get_with_slots(template_id)
        if not template:
            raise AppException(ErrorRegistry.PLAN_013)
        return self._to_read(template)

    def list_by_campus(self, campus_id: str) -> List[PlanningTemplateRead]:
        """Liste les templates d'un campus."""
        return [self._to_read(t) for t in self.repo.list_by_campus(campus_id)]

    def list_by_ministere(self, ministere_id: str) -> List[PlanningTemplateRead]:
        """Liste les templates d'un ministère."""
        return [self._to_read(t) for t in self.repo.list_by_ministere(ministere_id)]

    # ── Création depuis un planning ────────────────────────────────────

    def save_planning_as_template(
        self,
        planning_id: str,
        data: SaveAsTemplateRequest,
        created_by_id: str,
    ) -> PlanningTemplateRead:
        """Sauvegarde la structure d'un planning comme template.

        Capture : type activité, durée, créneaux (offsets relatifs),
        rôles uniques par créneau. Les membres sont ignorés.
        """
        planning = self._load_planning(planning_id)
        self._validate_for_template(planning)
        activite: Activite = planning.activite  # type: ignore[assignment]
        template = self._build_template(data, activite, created_by_id)
        self.db.add(template)
        self.db.flush()
        for slot in planning.slots:
            self._add_template_slot(template.id, slot, activite)
        self.db.flush()
        return self.get_template(template.id)

    # ── Mise à jour ────────────────────────────────────────────────────

    def update_template(
        self,
        template_id: str,
        data: PlanningTemplateUpdate,
    ) -> PlanningTemplateRead:
        """Met à jour nom et/ou description d'un template."""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise AppException(ErrorRegistry.PLAN_013)
        if data.nom is not None:
            template.nom = data.nom
        if data.description is not None:
            template.description = data.description
        self.db.add(template)
        self.db.flush()
        return self.get_template(template_id)

    # ── Suppression ────────────────────────────────────────────────────

    def delete_template(self, template_id: str) -> None:
        """Supprime un template (cascade sur slots et rôles)."""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise AppException(ErrorRegistry.PLAN_013)
        self.db.delete(template)
        self.db.flush()

    # ── Helpers privés ─────────────────────────────────────────────────

    def _load_planning(self, planning_id: str) -> PlanningService:
        """Charge un planning avec activité et créneaux+affectations."""
        stmt = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(
                selectinload(PlanningService.activite),  # type: ignore[arg-type]
                selectinload(  # type: ignore[arg-type]
                    PlanningService.slots  # type: ignore[arg-type]
                ).selectinload(
                    Slot.affectations  # type: ignore[arg-type]
                ),
            )
        )
        planning = self.db.exec(stmt).first()
        if not planning:
            raise AppException(ErrorRegistry.PLAN_014)
        return planning

    @staticmethod
    def _validate_for_template(planning: PlanningService) -> None:
        """Vérifie que le planning est éligible à la création de template."""
        if not planning.activite:
            raise AppException(ErrorRegistry.PLAN_014)
        if not planning.slots:
            raise AppException(ErrorRegistry.PLAN_014)

    @staticmethod
    def _compute_duree(activite: Activite) -> int:
        """Calcule la durée de l'activité en minutes."""
        delta = activite.date_fin - activite.date_debut
        return max(1, int(delta.total_seconds() // 60))

    def _build_template(
        self,
        data: SaveAsTemplateRequest,
        activite: Activite,
        created_by_id: str,
    ) -> PlanningTemplate:
        """Construit l'objet PlanningTemplate sans le persister."""
        return PlanningTemplate(
            nom=data.nom,
            description=data.description,
            activite_type=activite.type,
            duree_minutes=self._compute_duree(activite),
            campus_id=activite.campus_id,
            ministere_id=activite.ministere_organisateur_id,
            created_by_id=created_by_id,
        )

    def _add_template_slot(
        self,
        template_id: str,
        slot: Slot,
        activite: Activite,
    ) -> None:
        """Crée un PlanningTemplateSlot avec offsets relatifs."""
        offset_debut = max(
            0,
            int((slot.date_debut - activite.date_debut).total_seconds() // 60),
        )
        offset_fin = max(
            1,
            int((slot.date_fin - activite.date_debut).total_seconds() // 60),
        )
        tpl_slot = PlanningTemplateSlot(
            template_id=template_id,
            nom_creneau=slot.nom_creneau,
            offset_debut_minutes=offset_debut,
            offset_fin_minutes=offset_fin,
            nb_personnes_requis=slot.nb_personnes_requis,
        )
        self.db.add(tpl_slot)
        self.db.flush()
        self._add_slot_roles(tpl_slot.id, slot)

    def _add_slot_roles(self, tpl_slot_id: str, slot: Slot) -> None:
        """Crée les rôles dédupliqués pour un créneau de template."""
        seen: set[str] = set()
        for aff in slot.affectations:
            if aff.role_code not in seen:
                seen.add(aff.role_code)
                self.db.add(
                    PlanningTemplateRole(
                        slot_id=tpl_slot_id,
                        role_code=aff.role_code,
                    )
                )
        self.db.flush()

    @staticmethod
    def _to_read(template: PlanningTemplate) -> PlanningTemplateRead:
        """Convertit un ORM PlanningTemplate en DTO de lecture."""
        return PlanningTemplateRead(
            id=template.id,
            nom=template.nom,
            description=template.description,
            activite_type=template.activite_type,
            duree_minutes=template.duree_minutes,
            campus_id=template.campus_id,
            ministere_id=template.ministere_id,
            created_by_id=template.created_by_id,
            created_at=template.created_at,
            used_count=template.used_count,
            slots=[
                PlanningTemplateSlotRead(
                    id=s.id,
                    nom_creneau=s.nom_creneau,
                    offset_debut_minutes=s.offset_debut_minutes,
                    offset_fin_minutes=s.offset_fin_minutes,
                    nb_personnes_requis=s.nb_personnes_requis,
                    roles=[
                        PlanningTemplateRoleRead(id=r.id, role_code=r.role_code)
                        for r in s.roles
                    ],
                )
                for s in template.slots
            ],
        )
