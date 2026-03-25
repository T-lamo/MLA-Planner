"""Service de génération de plannings en série (US-98)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models.schema_db_model import Activite, PlanningService
from models.serie_model import (
    ConflitDate,
    GenerateSeriesPreviewRequest,
    GenerateSeriesRequest,
    GenerateSeriesResponse,
    PlanningSerieItem,
    SerieRecurrence,
    SeriesPreviewResponse,
)
from services.planning_template_service import PlanningTemplateSvc


def _nth_weekday_of_month(
    year: int, month: int, weekday: int, n: int
) -> Optional[date]:
    """Retourne la Nème occurrence de weekday dans le mois, ou None."""
    first_day = date(year, month, 1)
    days_ahead = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day + timedelta(days=days_ahead)
    target = first_occurrence + timedelta(weeks=n - 1)
    if target.month != month:
        return None
    return target


class SerieService:
    """Service de génération de plannings en série."""

    def __init__(self, db: Optional[Session]) -> None:
        self.db = db

    # ── Calcul des dates ──────────────────────────────────────────────────

    def compute_series_dates(self, request: GenerateSeriesPreviewRequest) -> List[date]:
        """Calcule la liste des dates selon la récurrence."""
        if request.date_fin < request.date_debut:
            raise AppException(ErrorRegistry.SERIE_002)
        if (
            request.recurrence == SerieRecurrence.HEBDOMADAIRE
            and request.jour_semaine is None
        ):
            raise AppException(ErrorRegistry.SERIE_003)

        if request.recurrence == SerieRecurrence.HEBDOMADAIRE:
            dates = self._compute_hebdomadaire(request)
        else:
            dates = self._compute_mensuelle(request)

        if len(dates) > 52:
            raise AppException(ErrorRegistry.SERIE_001)
        return dates

    def _compute_hebdomadaire(
        self, request: GenerateSeriesPreviewRequest
    ) -> List[date]:
        """Calcule les dates pour une récurrence hebdomadaire."""
        jour = request.jour_semaine
        assert jour is not None
        days_ahead = (jour - request.date_debut.weekday()) % 7
        current = request.date_debut + timedelta(days=days_ahead)
        dates: List[date] = []
        while current <= request.date_fin:
            dates.append(current)
            current += timedelta(weeks=1)
        return dates

    def _compute_mensuelle(self, request: GenerateSeriesPreviewRequest) -> List[date]:
        """Calcule les dates pour une récurrence mensuelle (Nème jour du mois)."""
        d = request.date_debut
        weekday = d.weekday()
        n = (d.day - 1) // 7 + 1
        dates: List[date] = [d]
        year, month = d.year, d.month
        while True:
            month += 1
            if month > 12:
                month = 1
                year += 1
            candidate = _nth_weekday_of_month(year, month, weekday, n)
            if candidate is None:
                continue
            if candidate > request.date_fin:
                break
            dates.append(candidate)
        return dates

    # ── Prévisualisation ─────────────────────────────────────────────────

    def get_series_preview(
        self,
        request: GenerateSeriesPreviewRequest,
        *,
        ministere_id: Optional[str],
    ) -> SeriesPreviewResponse:
        """Calcule les dates et détecte les conflits avec des plannings existants."""
        assert self.db is not None
        dates = self.compute_series_dates(request)
        conflits = (
            self._find_conflits(dates, ministere_id=ministere_id)
            if ministere_id
            else []
        )
        return SeriesPreviewResponse(dates=dates, total=len(dates), conflits=conflits)

    def _find_conflits(
        self,
        dates: List[date],
        *,
        ministere_id: str,
    ) -> List[ConflitDate]:
        """Détecte les plannings existants sur les dates cibles."""
        assert self.db is not None
        conflits: List[ConflitDate] = []
        for target_date in dates:
            conflit = self._check_date_conflit(target_date, ministere_id=ministere_id)
            if conflit is not None:
                conflits.append(conflit)
        return conflits

    def _check_date_conflit(
        self,
        target_date: date,
        *,
        ministere_id: str,
    ) -> Optional[ConflitDate]:
        """Vérifie si un planning existe déjà pour cette date/ministère."""
        assert self.db is not None
        day_start = datetime(
            target_date.year, target_date.month, target_date.day, 0, 0, 0
        )
        day_end = datetime(
            target_date.year, target_date.month, target_date.day, 23, 59, 59
        )
        stmt_a = select(Activite).where(
            Activite.ministere_organisateur_id == ministere_id,
            Activite.date_debut >= day_start,
            Activite.date_debut <= day_end,
        )
        activite = self.db.exec(stmt_a).first()
        if activite is None:
            return None
        stmt_p = select(PlanningService).where(
            PlanningService.activite_id == activite.id,
            PlanningService.deleted_at == None,  # noqa: E711
        )
        planning = self.db.exec(stmt_p).first()
        if planning is None:
            return None
        return ConflitDate(
            date=target_date,
            planning_id=planning.id,
            planning_titre=activite.type,
        )

    # ── Génération ───────────────────────────────────────────────────────

    def generate_series(
        self,
        request: GenerateSeriesRequest,
        *,
        created_by_id: str,
        ministere_id: str,
        campus_id: str,
    ) -> GenerateSeriesResponse:
        """Génère les plannings d'une série depuis un template."""
        assert self.db is not None
        dates = self.compute_series_dates(request)
        serie_id = str(uuid4())
        plannings: List[PlanningSerieItem] = []
        for target_date in dates:
            item = self._create_one_planning(
                request,
                target_date=target_date,
                serie_id=serie_id,
                created_by_id=created_by_id,
                ministere_id=ministere_id,
                campus_id=campus_id,
            )
            plannings.append(item)
        self.db.commit()
        return GenerateSeriesResponse(
            serie_id=serie_id, total=len(plannings), plannings=plannings
        )

    def _build_activite(
        self,
        target_date: date,
        *,
        ministere_id: str,
        campus_id: str,
        activite_type: str,
        duree_minutes: int,
    ) -> Activite:
        """Construit et persiste une Activite pour la date cible."""
        assert self.db is not None
        debut = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            9,
            0,
            0,
        )
        fin = debut + timedelta(minutes=duree_minutes)
        activite = Activite(
            type=activite_type,
            date_debut=debut,
            date_fin=fin,
            campus_id=campus_id,
            ministere_organisateur_id=ministere_id,
        )
        self.db.add(activite)
        self.db.flush()
        return activite

    def _build_planning(
        self,
        activite_id: str,
        *,
        template_id: str,
        serie_id: str,
    ) -> PlanningService:
        """Construit et persiste un PlanningService."""
        assert self.db is not None
        planning = PlanningService(
            activite_id=activite_id,
            statut_code="BROUILLON",
            template_id=template_id,
            serie_id=serie_id,
        )
        self.db.add(planning)
        self.db.flush()
        return planning

    def _create_one_planning(
        self,
        request: GenerateSeriesRequest,
        *,
        target_date: date,
        serie_id: str,
        created_by_id: str,
        ministere_id: str,
        campus_id: str,
    ) -> PlanningSerieItem:
        """Crée un planning avec ses créneaux depuis le template."""
        assert self.db is not None
        tpl_svc = PlanningTemplateSvc(self.db)
        template = tpl_svc.repo.get_with_slots(request.template_id)
        activite_type = template.activite_type if template else "Culte"
        duree = template.duree_minutes if template else 120
        activite = self._build_activite(
            target_date,
            ministere_id=ministere_id,
            campus_id=campus_id,
            activite_type=activite_type,
            duree_minutes=duree,
        )
        planning = self._build_planning(
            activite.id,
            template_id=request.template_id,
            serie_id=serie_id,
        )
        tpl_svc.apply_to_planning(request.template_id, planning.id)
        return PlanningSerieItem(
            id=planning.id,
            titre=activite_type,
            date_debut=target_date,
            statut="BROUILLON",
        )
