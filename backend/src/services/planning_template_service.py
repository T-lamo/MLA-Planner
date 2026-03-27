"""Service métier pour les templates de planning."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.auth.auth_utils import _role_name
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum import RoleName
from models.planning_template_model import (
    ApplyTemplateResult,
    PlanningTemplateFullUpdate,
    PlanningTemplateListItem,
    PlanningTemplateRead,
    PlanningTemplateRoleMembreRead,
    PlanningTemplateRoleRead,
    PlanningTemplateRoleWrite,
    PlanningTemplateSlotRead,
    PlanningTemplateSlotWrite,
    PlanningTemplateUpdate,
    SaveAsTemplateRequest,
    VisibiliteTemplate,
    WarningIndispo,
    WarningMembreIgnore,
)
from models.schema_db_model import (
    Activite,
    Affectation,
    Indisponibilite,
    Membre,
    PlanningService,
    PlanningTemplate,
    PlanningTemplateRole,
    PlanningTemplateRoleMembre,
    PlanningTemplateSlot,
    Slot,
    Utilisateur,
)
from repositories.planning_template_repository import (
    PlanningTemplateRepository,
)


def _get_user_role_names(user: Utilisateur) -> List[str]:
    """Extrait les noms Casbin des rôles d'un utilisateur."""
    return [
        _role_name(aff.role.libelle)
        for aff in user.affectations
        if aff.role and aff.role.libelle is not None
    ]


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

    # ── Liste bibliothèque US-95/99 ───────────────────────────────────

    def list_templates(
        self,
        user: Utilisateur,
        ministere_id_filter: Optional[str] = None,
    ) -> List[PlanningTemplateListItem]:
        """Liste les templates visibles par l'utilisateur, avec section.

        Visibilité (US-99) :
        - PRIVE     → créateur uniquement
        - MINISTERE → tous les responsables ayant accès à ce ministère
        - CAMPUS    → tous les responsables du campus
        Admin/Super Admin voient MINISTERE + CAMPUS + leurs propres PRIVE.
        """
        is_admin = _is_admin_or_super(user)
        campus_filter = self._resolve_campus_filter(user)
        membre = user.membre
        membre_id = str(membre.id) if membre else ""
        ministere_ids = [str(m.id) for m in membre.ministeres] if membre else []
        return self._fetch_templates_with_stats(
            campus_filter,
            ministere_id_filter,
            membre_id=membre_id,
            accessible_ministere_ids=ministere_ids,
            is_admin=is_admin,
        )

    def _resolve_campus_filter(self, user: Utilisateur) -> Optional[str]:
        """Retourne le campus_id à filtrer (None pour super admin sans campus)."""
        membre = user.membre
        campus_id = membre.campus_principal_id if membre else None
        if not campus_id and not _is_admin_or_super(user):
            raise AppException(ErrorRegistry.TMPL_005)
        return campus_id

    def _is_visible(
        self,
        tpl: PlanningTemplate,
        *,
        membre_id: str,
        accessible_ministere_ids: List[str],
        campus_filter: Optional[str],
        is_admin: bool,
    ) -> bool:
        """Retourne True si l'utilisateur peut voir ce template."""
        if tpl.created_by_id == membre_id:
            return True
        if tpl.visibilite == VisibiliteTemplate.PRIVE:
            return False
        if is_admin:
            return True
        if tpl.visibilite == VisibiliteTemplate.MINISTERE:
            return (
                tpl.campus_id == campus_filter
                and tpl.ministere_id in accessible_ministere_ids
            )
        if tpl.visibilite == VisibiliteTemplate.CAMPUS:
            return tpl.campus_id == campus_filter
        return False

    @staticmethod
    def _compute_section(tpl: PlanningTemplate, *, membre_id: str) -> str:
        """Retourne la section d'affichage (mes_templates/ministere/campus)."""
        if tpl.created_by_id == membre_id:
            return "mes_templates"
        if tpl.visibilite == VisibiliteTemplate.MINISTERE:
            return "ministere"
        return "campus"

    def _fetch_templates_with_stats(
        self,
        campus_filter: Optional[str],
        ministere_filter: Optional[str],
        *,
        membre_id: str,
        accessible_ministere_ids: List[str],
        is_admin: bool,
    ) -> List[PlanningTemplateListItem]:
        """Charge templates + filtre visibilité + calcule stats et section."""
        stmt = select(PlanningTemplate)
        if campus_filter:
            stmt = stmt.where(PlanningTemplate.campus_id == campus_filter)
        if ministere_filter:
            stmt = stmt.where(PlanningTemplate.ministere_id == ministere_filter)
        templates = list(self.db.exec(stmt).all())
        items: List[PlanningTemplateListItem] = []
        for tpl in templates:
            if not self._is_visible(
                tpl,
                membre_id=membre_id,
                accessible_ministere_ids=accessible_ministere_ids,
                campus_filter=campus_filter,
                is_admin=is_admin,
            ):
                continue
            stats = self._compute_usage_stats(tpl.id)
            nb_creneaux = self._compute_nb_creneaux(tpl.id)
            section = self._compute_section(tpl, membre_id=membre_id)
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
                    visibilite=tpl.visibilite,
                    section=section,
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
        if data.visibilite is not None:
            template.visibilite = data.visibilite
        self.db.add(template)
        self.db.flush()
        for slot_write in data.slots:
            self._create_slot_from_write(template.id, slot_write)
        self.db.flush()
        return self.get_template(template_id)

    def _delete_slots_and_roles(self, template: PlanningTemplate) -> None:
        """Supprime tous les créneaux (et leurs rôles/membres via cascade)."""
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
                membres = list(
                    self.db.exec(
                        select(PlanningTemplateRoleMembre).where(
                            PlanningTemplateRoleMembre.template_role_id == role.id
                        )
                    ).all()
                )
                for m in membres:
                    self.db.delete(m)
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
        for role_write in slot_write.roles:
            if role_write.role_code not in seen:
                seen.add(role_write.role_code)
                self._create_role_with_membres(tpl_slot.id, role_write, db=self.db)
        self.db.flush()

    def _create_role_with_membres(
        self,
        slot_id: str,
        role_write: PlanningTemplateRoleWrite,
        *,
        db: Session,
    ) -> PlanningTemplateRole:
        """Crée un PlanningTemplateRole avec ses membres suggérés."""
        role = PlanningTemplateRole(
            slot_id=slot_id,
            role_code=role_write.role_code,
        )
        db.add(role)
        db.flush()
        for membre_id in role_write.membres_suggeres_ids:
            if db.get(Membre, membre_id) is None:
                continue
            db.add(
                PlanningTemplateRoleMembre(
                    template_role_id=role.id,
                    membre_id=membre_id,
                )
            )
        return role

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
            visibilite=source.visibilite,
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
            visibilite=new_tpl.visibilite,
            section="mes_templates",
        )

    def _copy_slots(self, source: PlanningTemplate, new_template_id: str) -> None:
        """Copie tous les créneaux, rôles et membres suggérés du template."""
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
                new_role = PlanningTemplateRole(
                    slot_id=new_slot.id,
                    role_code=role.role_code,
                )
                self.db.add(new_role)
                self.db.flush()
                for ms in role.membres_suggeres:
                    self.db.add(
                        PlanningTemplateRoleMembre(
                            template_role_id=new_role.id,
                            membre_id=ms.membre_id,
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
        membre_id = str(membre.id) if membre else ""
        if template.created_by_id == membre_id:
            return
        if template.visibilite == VisibiliteTemplate.PRIVE:
            raise AppException(ErrorRegistry.TMPL_004)
        campus_id = membre.campus_principal_id if membre else None
        if template.visibilite == VisibiliteTemplate.CAMPUS:
            if template.campus_id != campus_id:
                raise AppException(ErrorRegistry.TMPL_004)
            return
        if template.visibilite == VisibiliteTemplate.MINISTERE:
            ministere_ids = (
                [str(m.id) for m in (membre.ministeres or [])] if membre else []
            )
            if (
                template.ministere_id not in ministere_ids
                or template.campus_id != campus_id
            ):
                raise AppException(ErrorRegistry.TMPL_004)
            return
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
            visibilite=data.visibilite,
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
    def _role_to_read(role: PlanningTemplateRole) -> PlanningTemplateRoleRead:
        """Convertit un ORM PlanningTemplateRole en DTO de lecture."""
        membres: List[PlanningTemplateRoleMembreRead] = []
        for ms in role.membres_suggeres:
            m = ms.membre
            if m is None:
                continue
            u = m.utilisateur
            membres.append(
                PlanningTemplateRoleMembreRead(
                    id=ms.id,
                    membre_id=ms.membre_id,
                    membre_nom=f"{m.prenom} {m.nom}",
                    membre_username=u.username if u else "",
                )
            )
        return PlanningTemplateRoleRead(
            id=role.id,
            role_code=role.role_code,
            membres_suggeres=membres,
        )

    # ── Application d'un template sur un planning US-96 ────────────────

    def apply_to_planning(
        self, template_id: str, planning_id: str
    ) -> ApplyTemplateResult:
        """Applique un template à un planning existant.

        Crée des slots et des affectations PROPOSE pour chaque membre suggéré
        éligible (actif, dans le bon ministère).
        Retourne un résultat avec warnings indispo et membres ignorés.
        """
        template = self.repo.get_with_slots(template_id)
        if not template:
            raise AppException(ErrorRegistry.TMPL_003)
        planning = self._load_planning_with_activite(planning_id)
        activite: Activite = planning.activite  # type: ignore[assignment]
        ministere_id = activite.ministere_organisateur_id
        planning_date = activite.date_debut.date()
        avertissements: List[WarningIndispo] = []
        ignores: List[WarningMembreIgnore] = []
        nb_creees = 0
        for tpl_slot in template.slots:
            slot = self._create_real_slot(planning_id, tpl_slot, activite)
            for role in tpl_slot.roles:
                counts = self._apply_role_membres(
                    role,
                    slot=slot,
                    ministere_id=ministere_id,
                    planning_date_str=str(planning_date),
                )
                nb_creees += counts[0]
                avertissements.extend(counts[1])
                ignores.extend(counts[2])
        self.db.flush()
        return ApplyTemplateResult(
            planning_id=planning_id,
            affectations_creees=nb_creees,
            avertissements_indispo=avertissements,
            membres_ignores=ignores,
        )

    def _load_planning_with_activite(self, planning_id: str) -> PlanningService:
        """Charge un planning avec son activité."""
        stmt = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(
                selectinload(PlanningService.activite),  # type: ignore[arg-type]
            )
        )
        planning = self.db.exec(stmt).first()
        if not planning or not planning.activite:
            raise AppException(ErrorRegistry.PLAN_014)
        return planning

    def _create_real_slot(
        self,
        planning_id: str,
        tpl_slot: PlanningTemplateSlot,
        activite: Activite,
    ) -> Slot:
        """Crée un Slot réel depuis un slot de template."""
        debut = activite.date_debut + timedelta(minutes=tpl_slot.offset_debut_minutes)
        fin = activite.date_debut + timedelta(minutes=tpl_slot.offset_fin_minutes)
        slot = Slot(
            planning_id=planning_id,
            nom_creneau=tpl_slot.nom_creneau,
            date_debut=debut,
            date_fin=fin,
            nb_personnes_requis=tpl_slot.nb_personnes_requis,
        )
        self.db.add(slot)
        self.db.flush()
        return slot

    def _apply_role_membres(
        self,
        role: PlanningTemplateRole,
        *,
        slot: Slot,
        ministere_id: str,
        planning_date_str: str,
    ) -> Tuple[int, List[WarningIndispo], List[WarningMembreIgnore]]:
        """Crée les affectations pour tous les membres suggérés d'un rôle."""
        nb = 0
        warns: List[WarningIndispo] = []
        ignores: List[WarningMembreIgnore] = []
        for ms in role.membres_suggeres:
            aff, w_i, w_ig = self._apply_membre_suggere(
                ms.membre_id,
                slot=slot,
                role_code=role.role_code,
                ministere_id=ministere_id,
                planning_date_str=planning_date_str,
            )
            if aff is not None:
                nb += 1
            if w_i is not None:
                warns.append(w_i)
            if w_ig is not None:
                ignores.append(w_ig)
        return nb, warns, ignores

    def _check_membre_eligibilite(
        self,
        membre: Membre,
        *,
        ministere_id: str,
    ) -> Optional[str]:
        """Retourne la raison d'exclusion ou None si éligible."""
        if not membre.actif:
            return "introuvable"
        ids = [str(m.id) for m in (membre.ministeres or [])]
        if ministere_id not in ids:
            return "hors_ministere"
        return None

    def _check_indisponibilite(
        self,
        *,
        membre_id: str,
        planning_date_str: str,
    ) -> bool:
        """Retourne True si le membre est indisponible à la date donnée."""
        stmt = select(Indisponibilite).where(
            Indisponibilite.membre_id == membre_id,
        )
        rows = self.db.exec(stmt).all()
        for row in rows:
            if row.date_debut is None or row.date_fin is None:
                continue
            if row.date_debut <= planning_date_str <= row.date_fin:
                return True
        return False

    def _apply_membre_suggere(
        self,
        membre_id: str,
        *,
        slot: Slot,
        role_code: str,
        ministere_id: str,
        planning_date_str: str,
    ) -> Tuple[
        Optional[Affectation],
        Optional[WarningIndispo],
        Optional[WarningMembreIgnore],
    ]:
        """Tente de créer une affectation pour un membre suggéré."""
        membre = self.db.get(Membre, membre_id)
        if membre is None:
            return (
                None,
                None,
                WarningMembreIgnore(
                    membre_id=membre_id,
                    membre_nom="Inconnu",
                    role_code=role_code,
                    raison="introuvable",
                ),
            )
        raison = self._check_membre_eligibilite(membre, ministere_id=ministere_id)
        if raison is not None:
            return (
                None,
                None,
                WarningMembreIgnore(
                    membre_id=membre_id,
                    membre_nom=f"{membre.prenom} {membre.nom}",
                    role_code=role_code,
                    raison=raison,
                ),
            )
        w_indispo: Optional[WarningIndispo] = None
        if self._check_indisponibilite(
            membre_id=membre_id,
            planning_date_str=planning_date_str,
        ):
            w_indispo = WarningIndispo(
                membre_id=membre_id,
                membre_nom=f"{membre.prenom} {membre.nom}",
                creneau_nom=slot.nom_creneau,
                role_code=role_code,
            )
        affectation = Affectation(
            slot_id=slot.id,
            membre_id=membre_id,
            role_code=role_code,
            statut_affectation_code="PROPOSE",
            ministere_id=ministere_id,
        )
        self.db.add(affectation)
        return affectation, w_indispo, None

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
            visibilite=template.visibilite,
            slots=[
                PlanningTemplateSlotRead(
                    id=s.id,
                    nom_creneau=s.nom_creneau,
                    offset_debut_minutes=s.offset_debut_minutes,
                    offset_fin_minutes=s.offset_fin_minutes,
                    nb_personnes_requis=s.nb_personnes_requis,
                    roles=[PlanningTemplateSvc._role_to_read(r) for r in s.roles],
                )
                for s in template.slots
            ],
        )
