"""Service métier pour les templates de planning."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import RoleName
from models.planning_template_model import (
    PlanningTemplateFullUpdate,
    PlanningTemplateListItem,
    PlanningTemplateRead,
    PlanningTemplateRoleRead,
    PlanningTemplateSlotRead,
    PlanningTemplateSlotWrite,
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
    Utilisateur,
)
from repositories.planning_template_repository import (
    PlanningTemplateRepository,
)


def _get_user_role_names(user: Utilisateur) -> List[str]:
    """Extrait les noms des rôles d'un utilisateur."""
    result: List[str] = []
    for aff in user.affectations:
        if aff.role and aff.role.libelle is not None:
            lib = aff.role.libelle
            if isinstance(lib, RoleName):
                result.append(lib.name)
            else:
                result.append(str(lib))
    return result


def _is_admin_or_super(user: Utilisateur) -> bool:
    """Vrai si l'user est ADMIN ou SUPER_ADMIN."""
    roles = _get_user_role_names(user)
    return RoleName.SUPER_ADMIN.name in roles or RoleName.ADMIN.name in roles


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

    # ── Liste bibliothèque US-95 ───────────────────────────────────────

    def list_templates(
        self,
        user: Utilisateur,
        ministere_id_filter: Optional[str] = None,
    ) -> List[PlanningTemplateListItem]:
        """Liste les templates avec stats d'usage.

        Admin/Super Admin : tous les templates du système.
        Responsable MLA   : uniquement ceux de son campus principal.
        """
        campus_filter = self._resolve_campus_filter(user)
        raw = self._fetch_templates_with_stats(campus_filter, ministere_id_filter)
        return raw

    def _resolve_campus_filter(self, user: Utilisateur) -> Optional[str]:
        """Retourne le campus_id à filtrer, ou None si admin."""
        if _is_admin_or_super(user):
            return None
        membre = user.membre
        campus_id = membre.campus_principal_id if membre else None
        if not campus_id:
            raise AppException(ErrorRegistry.TMPL_005)
        return campus_id

    def _fetch_templates_with_stats(
        self,
        campus_filter: Optional[str],
        ministere_filter: Optional[str],
    ) -> List[PlanningTemplateListItem]:
        """Charge templates + calcule nb_creneaux, usage_count, last_used."""
        stmt = select(PlanningTemplate)
        if campus_filter:
            stmt = stmt.where(PlanningTemplate.campus_id == campus_filter)
        if ministere_filter:
            stmt = stmt.where(PlanningTemplate.ministere_id == ministere_filter)
        templates = list(self.db.exec(stmt).all())
        items: List[PlanningTemplateListItem] = []
        for tpl in templates:
            stats = self._compute_usage_stats(tpl.id)
            nb_creneaux = self._compute_nb_creneaux(tpl.id)
            items.append(
                PlanningTemplateListItem(
                    id=tpl.id,
                    nom=tpl.nom,
                    description=tpl.description,
                    ministere_id=tpl.ministere_id,
                    campus_id=tpl.campus_id,
                    activite_type=tpl.activite_type,
                    nb_creneaux=nb_creneaux,
                    usage_count=stats[0],
                    last_used_at=stats[1],
                    created_at=tpl.created_at,
                )
            )
        items.sort(
            key=lambda x: (
                x.last_used_at is None,
                -(x.last_used_at.timestamp() if x.last_used_at else 0),
            )
        )
        return items

    def _compute_usage_stats(self, template_id: str) -> tuple[int, Optional[datetime]]:
        """Retourne (usage_count, last_used_at) depuis t_planningservice."""
        count_stmt = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(PlanningService)
            .where(
                PlanningService.template_id == template_id,
                PlanningService.deleted_at == None,  # noqa: E711
            )
        )
        count = self.db.exec(count_stmt).one()

        max_stmt = select(func.max(Activite.date_debut)).where(
            PlanningService.template_id == template_id,
            PlanningService.activite_id == Activite.id,
            PlanningService.deleted_at == None,  # noqa: E711
        )
        last_used = self.db.exec(max_stmt).one()
        return (count or 0, last_used)

    def _compute_nb_creneaux(self, template_id: str) -> int:
        """Retourne le nombre de créneaux du template."""
        stmt = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(PlanningTemplateSlot)
            .where(PlanningTemplateSlot.template_id == template_id)
        )
        result = self.db.exec(stmt).one()
        return result or 0

    # ── Lecture full US-95 ─────────────────────────────────────────────

    def get_template_full(
        self, template_id: str, user: Utilisateur
    ) -> PlanningTemplateRead:
        """Charge un template complet (slots + rôles) avec vérif accès."""
        template = self.repo.get_with_slots(template_id)
        if not template:
            raise AppException(ErrorRegistry.TMPL_003)
        self._check_template_access(template, user)
        return self._to_read(template)

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

    # ── Mise à jour complète US-95 ─────────────────────────────────────

    def update_template_full(
        self,
        template_id: str,
        data: PlanningTemplateFullUpdate,
        user: Utilisateur,
    ) -> PlanningTemplateRead:
        """Remplace nom, description et recréé tous les créneaux/rôles."""
        template = self.repo.get_with_slots(template_id)
        if not template:
            raise AppException(ErrorRegistry.TMPL_003)
        self._check_template_access(template, user)
        self._delete_slots_and_roles(template)
        self.db.expire(template)
        template.nom = data.nom
        template.description = data.description
        self.db.add(template)
        self.db.flush()
        for slot_write in data.slots:
            self._create_slot_from_write(template.id, slot_write)
        self.db.flush()
        return self.get_template(template_id)

    def _delete_slots_and_roles(self, template: PlanningTemplate) -> None:
        """Supprime tous les créneaux (et leurs rôles via cascade) du template."""
        slots = list(
            self.db.exec(
                select(PlanningTemplateSlot).where(
                    PlanningTemplateSlot.template_id == template.id
                )
            ).all()
        )
        for slot in slots:
            roles = list(
                self.db.exec(
                    select(PlanningTemplateRole).where(
                        PlanningTemplateRole.slot_id == slot.id
                    )
                ).all()
            )
            for role in roles:
                self.db.delete(role)
            self.db.delete(slot)
        self.db.flush()

    def _create_slot_from_write(
        self, template_id: str, slot_write: PlanningTemplateSlotWrite
    ) -> None:
        """Crée un PlanningTemplateSlot avec ses rôles depuis un SlotWrite."""
        tpl_slot = PlanningTemplateSlot(
            template_id=template_id,
            nom_creneau=slot_write.nom_creneau,
            offset_debut_minutes=slot_write.offset_debut_minutes,
            offset_fin_minutes=slot_write.offset_fin_minutes,
            nb_personnes_requis=slot_write.nb_personnes_requis,
        )
        self.db.add(tpl_slot)
        self.db.flush()
        seen: set[str] = set()
        for role_code in slot_write.roles:
            if role_code not in seen:
                seen.add(role_code)
                self.db.add(
                    PlanningTemplateRole(
                        slot_id=tpl_slot.id,
                        role_code=role_code,
                    )
                )
        self.db.flush()

    # ── Mise à jour partielle (nom/desc) ───────────────────────────────

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

    # ── Duplication US-95 ─────────────────────────────────────────────

    def duplicate_template(
        self, template_id: str, user: Utilisateur
    ) -> PlanningTemplateListItem:
        """Duplique un template (nom + ' (copie)')."""
        source = self.repo.get_with_slots(template_id)
        if not source:
            raise AppException(ErrorRegistry.TMPL_003)
        self._check_template_access(source, user)
        member_id = user.membre.id if user.membre else ""
        new_tpl = PlanningTemplate(
            id=str(uuid4()),
            nom=f"{source.nom} (copie)",
            description=source.description,
            activite_type=source.activite_type,
            duree_minutes=source.duree_minutes,
            campus_id=source.campus_id,
            ministere_id=source.ministere_id,
            created_by_id=member_id,
        )
        self.db.add(new_tpl)
        self.db.flush()
        self._copy_slots(source, new_tpl.id)
        stats = self._compute_usage_stats(new_tpl.id)
        nb = self._compute_nb_creneaux(new_tpl.id)
        return PlanningTemplateListItem(
            id=new_tpl.id,
            nom=new_tpl.nom,
            description=new_tpl.description,
            ministere_id=new_tpl.ministere_id,
            campus_id=new_tpl.campus_id,
            activite_type=new_tpl.activite_type,
            nb_creneaux=nb,
            usage_count=stats[0],
            last_used_at=stats[1],
            created_at=new_tpl.created_at,
        )

    def _copy_slots(self, source: PlanningTemplate, new_template_id: str) -> None:
        """Copie tous les créneaux et rôles du template source."""
        for slot in source.slots:
            new_slot = PlanningTemplateSlot(
                template_id=new_template_id,
                nom_creneau=slot.nom_creneau,
                offset_debut_minutes=slot.offset_debut_minutes,
                offset_fin_minutes=slot.offset_fin_minutes,
                nb_personnes_requis=slot.nb_personnes_requis,
            )
            self.db.add(new_slot)
            self.db.flush()
            for role in slot.roles:
                self.db.add(
                    PlanningTemplateRole(
                        slot_id=new_slot.id,
                        role_code=role.role_code,
                    )
                )
        self.db.flush()

    # ── Suppression US-95 ─────────────────────────────────────────────

    def delete_template_with_access(self, template_id: str, user: Utilisateur) -> None:
        """Supprime un template après vérification d'accès.

        Nullifie template_id sur les plannings liés avant suppression.
        """
        template = self.repo.get_by_id(template_id)
        if not template:
            raise AppException(ErrorRegistry.TMPL_003)
        self._check_template_access(template, user)
        self._nullify_planning_template_refs(template_id)
        self._delete_slots_and_roles(template)
        self.db.delete(template)
        self.db.flush()

    def _nullify_planning_template_refs(self, template_id: str) -> None:
        """Nullifie template_id sur tous les plannings liés."""
        plannings = list(
            self.db.exec(
                select(PlanningService).where(
                    PlanningService.template_id == template_id
                )
            ).all()
        )
        for p in plannings:
            p.template_id = None
            self.db.add(p)
        self.db.flush()

    # ── Suppression (ancienne, sans contrôle accès) ────────────────────

    def delete_template(self, template_id: str) -> None:
        """Supprime un template (cascade sur slots et rôles)."""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise AppException(ErrorRegistry.PLAN_013)
        self.db.delete(template)
        self.db.flush()

    # ── Helpers privés ─────────────────────────────────────────────────

    def _check_template_access(
        self, template: PlanningTemplate, user: Utilisateur
    ) -> None:
        """Lève TMPL_004 si l'utilisateur n'a pas accès au template."""
        if _is_admin_or_super(user):
            return
        membre = user.membre
        campus_id = membre.campus_principal_id if membre else None
        if template.campus_id != campus_id:
            raise AppException(ErrorRegistry.TMPL_004)

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
