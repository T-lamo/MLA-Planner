import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, Sequence, cast

from fastapi import BackgroundTasks
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from core.workflow_engine import WorkflowEngine, planning_transitions
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    Affectation,
    PlanningService,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    Slot,
    SlotCreate,
)
from models.activite_model import ActiviteFullRead
from models.membre_model import MemberAgendaResponse
from models.planning_model import (
    PlanningFullCreate,
    PlanningFullRead,
    PlanningFullUpdate,
    ViewContext,
)
from models.schema_db_model import Activite, Campus, Ministere, PlanningTemplate
from notification.notification_schemas import (
    PlanningCancelledNotification,
    PlanningPublishedNotification,
)
from notification.notification_service import EmailService
from repositories.planning_repository import PlanningRepository
from repositories.planning_template_repository import PlanningTemplateRepository
from services.activite_service import ActiviteService
from services.slot_service import SlotService
from utils.utils_func import extract_field

from .base_service import BaseService

logger = logging.getLogger(__name__)


class PlanningServiceSvc(
    BaseService[
        PlanningServiceCreate,
        PlanningServiceRead,
        PlanningServiceUpdate,
        PlanningService,
    ]
):
    def __init__(self, db: Session):
        super().__init__(PlanningRepository(db), "Planning")
        self.db = db
        self.workflow = WorkflowEngine[PlanningStatusCode](planning_transitions)

        # Injection des services dépendants pour éviter les réinstanciations
        self.activite_svc = ActiviteService(self.db)
        self.slot_svc = SlotService(self.db)

    def _collect_notification_data_published(
        self, planning_id: str
    ) -> List[PlanningPublishedNotification]:
        """Construit la liste des notifications de publication (1 par affectation)."""
        query = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(
                selectinload(cast(Any, PlanningService.activite)),
                selectinload(cast(Any, PlanningService.slots))
                .selectinload(cast(Any, Slot.affectations))
                .selectinload(cast(Any, Affectation.membre)),
            )
        )
        planning = self.db.exec(query).first()
        if not planning or not planning.activite:
            return []
        activite = planning.activite
        campus_nom, ministere_nom = self._resolve_activite_names(
            activite.campus_id, activite.ministere_organisateur_id
        )
        notifications: List[PlanningPublishedNotification] = []
        for slot in planning.slots:
            heure_debut = slot.date_debut.strftime("%H:%M")
            heure_fin = slot.date_fin.strftime("%H:%M")
            for aff in slot.affectations:
                membre = aff.membre
                if not membre or not membre.email:
                    continue
                notifications.append(
                    PlanningPublishedNotification(
                        email=membre.email,
                        prenom=membre.prenom,
                        nom=membre.nom,
                        type_activite=activite.type,
                        date_activite=activite.date_debut.date(),
                        heure_debut=heure_debut,
                        heure_fin=heure_fin,
                        lieu=activite.lieu,
                        campus_nom=campus_nom or "",
                        ministere_nom=ministere_nom or "",
                        nom_creneau=slot.nom_creneau,
                        role_code=aff.role_code,
                        date_debut_dt=slot.date_debut,
                        date_fin_dt=slot.date_fin,
                    )
                )
        return notifications

    def _collect_notification_data_cancelled(
        self, planning_id: str, motif: Optional[str] = None
    ) -> List[PlanningCancelledNotification]:
        """Construit la liste des notifications d'annulation (1 par membre unique)."""
        query = (
            select(PlanningService)
            .where(PlanningService.id == planning_id)
            .options(
                selectinload(cast(Any, PlanningService.activite)),
                selectinload(cast(Any, PlanningService.slots))
                .selectinload(cast(Any, Slot.affectations))
                .selectinload(cast(Any, Affectation.membre)),
            )
        )
        planning = self.db.exec(query).first()
        if not planning or not planning.activite:
            return []
        activite = planning.activite
        campus_nom, ministere_nom = self._resolve_activite_names(
            activite.campus_id, activite.ministere_organisateur_id
        )
        type_activite = activite.type
        date_activite = activite.date_debut.date()
        seen: set[str] = set()
        notifications: List[PlanningCancelledNotification] = []
        for slot in planning.slots:
            for aff in slot.affectations:
                membre = aff.membre
                if not membre or not membre.email or membre.id in seen:
                    continue
                seen.add(membre.id)
                notifications.append(
                    PlanningCancelledNotification(
                        email=membre.email,
                        prenom=membre.prenom,
                        nom=membre.nom,
                        type_activite=type_activite,
                        date_activite=date_activite,
                        campus_nom=campus_nom or "",
                        ministere_nom=ministere_nom or "",
                        motif=motif,
                    )
                )
        return notifications

    def _dispatch_status_notifications(
        self,
        planning_id: str,
        new_status: PlanningStatusCode,
        background_tasks: BackgroundTasks,
        email_service: EmailService,
    ) -> None:
        """Enqueue les emails de notification selon le nouveau statut."""
        if new_status == PlanningStatusCode.PUBLIE:
            notifs_p = self._collect_notification_data_published(planning_id)
            for np in notifs_p:
                background_tasks.add_task(email_service.notify_planning_published, np)
        elif new_status == PlanningStatusCode.ANNULE:
            notifs_a = self._collect_notification_data_cancelled(planning_id)
            for na in notifs_a:
                background_tasks.add_task(email_service.notify_planning_cancelled, na)

    def _resolve_activite_names(
        self, campus_id: str, ministere_id: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Résout les noms du campus et du ministère organisateur."""
        campus = self.db.get(Campus, campus_id)
        ministere = self.db.get(Ministere, ministere_id)
        return (
            campus.nom if campus else None,
            ministere.nom if ministere else None,
        )

    def _enrich_plannings_list(
        self, plannings: Sequence[PlanningService]
    ) -> List[PlanningFullRead]:
        """Valide et enrichit chaque planning avec les noms résolus du campus
        et du ministère organisateur (campus_nom, ministere_organisateur_nom)."""
        result = []
        for p in plannings:
            dto = PlanningFullRead.model_validate(p)
            if p.activite:
                dto.activite = self._build_activite_full(p.activite)
            result.append(dto)
        return result

    def _build_activite_full(self, activite: Activite) -> ActiviteFullRead:
        """Construit un ActiviteFullRead avec noms résolus."""
        campus_nom, ministere_nom = self._resolve_activite_names(
            activite.campus_id, activite.ministere_organisateur_id
        )
        return ActiviteFullRead(
            id=activite.id,
            type=activite.type,
            date_debut=activite.date_debut,
            date_fin=activite.date_fin,
            lieu=activite.lieu,
            description=activite.description,
            campus_id=activite.campus_id,
            ministere_organisateur_id=activite.ministere_organisateur_id,
            campus_nom=campus_nom,
            ministere_organisateur_nom=ministere_nom,
        )

    def _has_affectations(self, planning_id: str) -> bool:
        """Vérifie si au moins une affectation existe pour ce planning."""
        query = (
            select(Affectation)
            .join(
                Slot,
                col(cast(Any, Slot.id)) == col(cast(Any, Affectation.slot_id)),
            )
            .where(Slot.planning_id == planning_id)
        )
        return self.db.exec(query).first() is not None

    def update_planning_status(
        self,
        planning_id: str,
        new_status: PlanningStatusCode,
        auto_flush: bool = True,
        *,
        background_tasks: Optional[BackgroundTasks] = None,
        email_service: Optional[EmailService] = None,
    ) -> PlanningService:
        """Met à jour le statut avec gestion du workflow et notifications."""
        planning = self.get_one(planning_id)
        current_status = PlanningStatusCode(planning.statut_code)

        if new_status == PlanningStatusCode.PUBLIE:
            if not self._has_affectations(planning_id):
                raise AppException(ErrorRegistry.PLANNING_CANT_PUBLISH)

        self.workflow.execute_transition(current_status, new_status)
        planning.statut_code = new_status.value
        self.db.add(planning)

        if new_status == PlanningStatusCode.PUBLIE:
            self._on_publish_hook(planning)

        if auto_flush:
            self.db.flush()

        if background_tasks and email_service:
            self._dispatch_status_notifications(
                planning_id, new_status, background_tasks, email_service
            )

        return planning

    def _on_publish_hook(self, planning: PlanningService) -> None:
        """Hook appelé lors du passage au statut PUBLIE, avant le flush.

        No-op par défaut. Peut être surchargé ou monkeypatché en test
        pour simuler des effets de bord (ex : envoi email) et vérifier
        l'atomicité du rollback.
        """

    def create_slot(self, slot_data: SlotCreate) -> Slot:
        """Délégué au SlotService."""
        return self.slot_svc.add_slot_to_planning(slot_data.planning_id, slot_data)

    def _increment_template_usage(self, template_id: str) -> None:
        """Incrémente used_count du template utilisé lors de la création."""
        PlanningTemplateRepository(self.db).increment_used_count(template_id)

    def create_full_planning(self, data: PlanningFullCreate) -> PlanningService:
        """Crée un planning complet (Activité + Planning
        + Slots + Affectations) de façon atomique."""
        logger.info("Début création planning complet")
        try:
            # 1. Création de l'Activité
            activite_db = self.activite_svc.create(data.activite)

            # 2. Création du Planning
            statut_initial = extract_field(
                data.planning, "statut_code", PlanningStatusCode.BROUILLON.value
            )

            p_create = PlanningServiceCreate(
                activite_id=activite_db.id, statut_code=statut_initial
            )
            planning_db = self.create(p_create)

            # 3. Synchronisation des Slots & Affectations
            self.slot_svc.sync_planning_slots(planning_db.id, data.slots)

            self.db.flush()

            # 4. Liaison template et incrément du compteur
            if data.template_id:
                tpl = self.db.get(PlanningTemplate, data.template_id)
                if tpl:
                    planning_db.template_id = data.template_id
                    self.db.add(planning_db)
                    self.db.flush()
                    self._increment_template_usage(data.template_id)

            self.db.refresh(planning_db)
            return planning_db

        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_CREATION_ERROR.message.format(error=str(e))
            )
            raise e

    def update_full_planning(
        self, planning_id: str, data: PlanningFullUpdate
    ) -> PlanningService:
        planning = self.get_one(planning_id)

        if planning.statut_code in [
            PlanningStatusCode.TERMINE.value,
            PlanningStatusCode.ANNULE.value,
        ]:
            raise AppException(
                ErrorRegistry.PLANNING_IMMUTABLE, status=planning.statut_code
            )

        try:
            # 1. Mise à jour du Statut
            new_status_code = extract_field(data.planning, "statut_code")
            if new_status_code and new_status_code != planning.statut_code:
                self.update_planning_status(
                    planning_id, PlanningStatusCode(new_status_code), auto_flush=False
                )

            # 2. Mise à jour de l'Activité
            if data.activite:
                if not planning.activite_id:
                    raise AppException(ErrorRegistry.PLANNING_ACTIVITY_MISSING)

                self.activite_svc.update(str(planning.activite_id), data.activite)

            # 3. Synchronisation Slots (ignoré si non fourni)
            if data.slots is not None:
                self.slot_svc.sync_planning_slots(planning.id, data.slots)

            self.db.flush()
            self.db.refresh(planning)
            return planning

        except AppException:
            # On laisse remonter nos exceptions métier typées
            raise
        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_UPDATE_ERROR.message.format(
                    id=planning_id, error=str(e)
                )
            )
            raise e

    def delete_full_planning(self, planning_id: str) -> None:
        planning = self.get_one(planning_id)
        activite_id = planning.activite_id

        if planning.statut_code == PlanningStatusCode.PUBLIE.value:
            raise AppException(
                ErrorRegistry.PLANNING_DELETE_IMPOSSIBLE, status=planning.statut_code
            )

        try:
            self.slot_svc.delete_by_planning(planning_id)
            self.db.delete(planning)
            self.db.flush()

            if not activite_id:
                logger.warning(
                    ErrorRegistry.PLANNING_DELETED_WITHOUT_ACTIVITY.message.format(
                        id=planning_id
                    )
                )
            else:
                self.activite_svc.hard_delete(str(activite_id))

            logger.info(f"Full Delete réussi : Planning {planning_id}")
        except AppException:
            raise
        except Exception as e:
            logger.error(
                ErrorRegistry.PLANNING_FATAL_DELETE_ERROR.message.format(
                    id=planning_id, error=str(e)
                )
            )
            raise e

    # Dans la classe PlanningServiceSvc :

    def get_full_planning(self, planning_id: str) -> PlanningFullRead:
        try:
            # 1. Fetch optimisé (La requête reste ici
            # car elle définit le périmètre du DTO)
            query = (
                select(PlanningService)
                .where(PlanningService.id == planning_id)
                .where(
                    PlanningService.deleted_at == None  # noqa: E711
                )  # pylint: disable=C0121
                .options(
                    selectinload(cast(Any, PlanningService.activite)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.membre)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.ministere)),
                )
            )
            planning_db = self.db.exec(query).first()

            if not planning_db:
                raise AppException(ErrorRegistry.PLAN_NOT_FOUND)

            # 2. Délégation aux services spécialisés
            total, filled = self.slot_svc.get_slots_metrics(planning_db.slots)

            # 3. Calcul du Workflow (propre au Planning)
            current_status = PlanningStatusCode(planning_db.statut_code)
            allowed = self.workflow.get_allowed_transitions(current_status)

            context = ViewContext(
                allowed_transitions=[s.value for s in allowed],
                total_slots=total,
                filled_slots=filled,
                is_ready_for_publish=(total > 0 and filled == total),
            )

            # 4. Assemblage final
            result_dto = PlanningFullRead.model_validate(planning_db)
            if planning_db.activite:
                result_dto.activite = self._build_activite_full(planning_db.activite)
            result_dto.view_context = context
            return result_dto

        except Exception as e:
            logger.error(f"Erreur get_full_planning ID {planning_id}: {str(e)}")
            raise

    def list_by_ministere(
        self,
        ministere_id: str,
        campus_id: Optional[str] = None,
    ) -> List[PlanningFullRead]:
        """Retourne tous les plannings complets dont l'activité est organisée
        par un ministère donné, avec activite + slots + affectations chargés."""
        cutoff = datetime.now() - timedelta(days=7)
        try:
            query = (
                select(PlanningService)
                .join(Activite)
                .where(Activite.ministere_organisateur_id == ministere_id)
                .where(Activite.date_debut >= cutoff)
                .where(
                    PlanningService.deleted_at == None  # noqa: E711
                )  # pylint: disable=C0121
                .options(
                    selectinload(cast(Any, PlanningService.activite)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.membre)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.ministere)),
                )
            )
            if campus_id:
                query = query.where(Activite.campus_id == campus_id)
            results = self.db.exec(query).unique().all()
            return self._enrich_plannings_list(results)
        except Exception as e:
            logger.error(f"Erreur list_by_ministere {ministere_id}: {str(e)}")
            raise

    def list_my_plannings_full(
        self,
        membre_id: str,
        campus_id: Optional[str] = None,
    ) -> List[PlanningFullRead]:
        """Retourne tous les plannings complets où l'utilisateur connecté
        est affecté dans au moins un slot (vue calendrier personnelle)."""
        cutoff = datetime.now() - timedelta(days=7)
        try:
            query = (
                select(PlanningService)
                .join(cast(Any, PlanningService.slots))
                .join(cast(Any, Slot.affectations))
                .join(
                    Activite,
                    cast(Any, PlanningService.activite_id) == cast(Any, Activite.id),
                )
                .where(Affectation.membre_id == membre_id)
                .where(Activite.date_debut >= cutoff)
                .where(
                    PlanningService.deleted_at == None  # noqa: E711
                )  # pylint: disable=C0121
                .options(
                    selectinload(cast(Any, PlanningService.activite)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.membre)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.ministere)),
                )
            )
            if campus_id:
                query = query.where(Activite.campus_id == campus_id)
            results = self.db.exec(query).unique().all()
            return self._enrich_plannings_list(results)
        except Exception as e:
            logger.error(f"Erreur list_my_plannings_full {membre_id}: {str(e)}")
            raise

    def list_by_campus(self, campus_id: str) -> List[PlanningFullRead]:
        """Retourne tous les plannings complets dont l'activité se déroule
        sur un campus donné, avec activite + slots + affectations chargés."""
        cutoff = datetime.now() - timedelta(days=7)
        try:
            query = (
                select(PlanningService)
                .join(Activite)
                .where(Activite.campus_id == campus_id)
                .where(Activite.date_debut >= cutoff)
                .where(
                    PlanningService.deleted_at == None  # noqa: E711
                )  # pylint: disable=C0121
                .options(
                    selectinload(cast(Any, PlanningService.activite)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.membre)),
                    selectinload(cast(Any, PlanningService.slots))
                    .selectinload(cast(Any, Slot.affectations))
                    .selectinload(cast(Any, Affectation.ministere)),
                )
            )
            results = self.db.exec(query).unique().all()
            return self._enrich_plannings_list(results)
        except Exception as e:
            logger.error(f"Erreur list_by_campus {campus_id}: {str(e)}")
            raise

    def get_member_agenda_full(
        self, membre_id: str, campus_id: str, start: datetime, end: datetime
    ):
        # 1. Requête SQL avec jointures (optimisation des performances)
        query = (
            select(Affectation)
            .join(Slot)
            .join(PlanningService)
            .join(Activite)
            .where(Affectation.membre_id == membre_id)
            .where(Activite.campus_id == campus_id)
            .where(Slot.date_debut >= start)
            .where(Slot.date_debut <= end)
            .options(
                selectinload(cast(Any, Affectation.slot))
                .selectinload(cast(Any, Slot.planning))
                .selectinload(cast(Any, PlanningService.activite))
                .selectinload(cast(Any, Activite.campus))
            )
        )
        results = self.db.exec(query).all()
        affectations = list(results)

        # 2. Appel au SlotService (qui lui-même appellera AffectationService)
        entries = self.slot_svc.map_affectations_to_entries(affectations)
        stats = self.slot_svc.get_agenda_statistics(affectations)

        # 3. Rassemblement final
        return MemberAgendaResponse(
            period_start=start, period_end=end, statistics=stats, entries=entries
        )
