"""Tests unitaires et d'intégration pour la génération de séries (US-98)."""

# pylint: disable=redefined-outer-name,duplicate-code

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Activite, PlanningService
from models.schema_db_model import (
    Membre,
    PlanningTemplate,
    PlanningTemplateRole,
    PlanningTemplateRoleMembre,
    PlanningTemplateSlot,
)
from models.serie_model import (
    GenerateSeriesPreviewRequest,
    GenerateSeriesRequest,
    SerieRecurrence,
)
from services.serie_service import SerieService

# ---------------------------------------------------------------------------
# Fixtures locales
# ---------------------------------------------------------------------------


@pytest.fixture
def template_serie(
    session: Session, test_campus, test_ministere, test_membre
) -> PlanningTemplate:
    """Template complet avec 1 slot et 1 rôle pour les tests de série."""
    tpl = PlanningTemplate(
        nom="Template Série Test",
        description=None,
        activite_type="Culte",
        duree_minutes=120,
        campus_id=test_campus.id,
        ministere_id=test_ministere.id,
        created_by_id=test_membre.id,
    )
    session.add(tpl)
    session.flush()
    slot = PlanningTemplateSlot(
        template_id=tpl.id,
        nom_creneau="Louange",
        offset_debut_minutes=0,
        offset_fin_minutes=60,
        nb_personnes_requis=1,
    )
    session.add(slot)
    session.flush()
    role = PlanningTemplateRole(slot_id=slot.id, role_code="TENOR")
    session.add(role)
    session.flush()
    session.refresh(tpl)
    return tpl


@pytest.fixture
def membre_ministere_serie(session: Session, test_campus, test_ministere) -> Membre:
    """Membre actif lié au test_ministere pour tests de série."""
    m = Membre(
        nom=f"SerieTest{uuid4().hex[:4]}",
        prenom="Membre",
        email=f"serie_{uuid4().hex[:6]}@test.com",
        actif=True,
    )
    m.campuses = [test_campus]
    m.ministeres = [test_ministere]
    session.add(m)
    session.flush()
    return m


@pytest.fixture
def template_serie_avec_membre(
    session: Session,
    test_campus,
    test_ministere,
    test_membre,
    membre_ministere_serie,
) -> PlanningTemplate:
    """Template avec 1 slot, 1 rôle, 1 membre suggéré éligible."""
    tpl = PlanningTemplate(
        nom="Template Série Membre",
        description=None,
        activite_type="Culte",
        duree_minutes=120,
        campus_id=test_campus.id,
        ministere_id=test_ministere.id,
        created_by_id=test_membre.id,
    )
    session.add(tpl)
    session.flush()
    slot = PlanningTemplateSlot(
        template_id=tpl.id,
        nom_creneau="Accueil",
        offset_debut_minutes=0,
        offset_fin_minutes=60,
        nb_personnes_requis=1,
    )
    session.add(slot)
    session.flush()
    role = PlanningTemplateRole(slot_id=slot.id, role_code="ACCUEIL")
    session.add(role)
    session.flush()
    session.add(
        PlanningTemplateRoleMembre(
            template_role_id=role.id,
            membre_id=membre_ministere_serie.id,
        )
    )
    session.flush()
    session.refresh(tpl)
    return tpl


# ---------------------------------------------------------------------------
# Tests unitaires — compute_series_dates (sans DB)
# ---------------------------------------------------------------------------


def test_compute_series_hebdomadaire():
    """4 lundis consécutifs à partir du 6 jan 2025."""
    svc = SerieService(db=None)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2025, 1, 6),
        date_fin=date(2025, 1, 27),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=0,
    )
    dates = svc.compute_series_dates(req)
    assert len(dates) == 4
    assert all(d.weekday() == 0 for d in dates)


def test_compute_series_mensuelle_nieme_position():
    """1er lundi de jan/fév/mars 2025."""
    svc = SerieService(db=None)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2025, 1, 6),
        date_fin=date(2025, 3, 31),
        recurrence=SerieRecurrence.MENSUELLE,
        jour_semaine=None,
    )
    dates = svc.compute_series_dates(req)
    assert len(dates) == 3
    for d in dates:
        assert d.weekday() == 0
        assert d.day <= 7


def test_compute_series_limite_52():
    """Plus de 52 dates (1 an hebdomadaire) → SERIE_001."""
    svc = SerieService(db=None)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2025, 1, 6),
        date_fin=date(2026, 3, 31),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=0,
    )
    with pytest.raises(AppException) as exc:
        svc.compute_series_dates(req)
    assert exc.value.code == ErrorRegistry.SERIE_001.code


def test_compute_series_date_fin_invalide():
    """date_fin < date_debut → SERIE_002."""
    svc = SerieService(db=None)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2025, 3, 1),
        date_fin=date(2025, 1, 1),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=0,
    )
    with pytest.raises(AppException) as exc:
        svc.compute_series_dates(req)
    assert exc.value.code == ErrorRegistry.SERIE_002.code


def test_compute_series_hebdo_sans_jour():
    """HEBDOMADAIRE sans jour_semaine → SERIE_003."""
    svc = SerieService(db=None)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2025, 1, 6),
        date_fin=date(2025, 1, 27),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=None,
    )
    with pytest.raises(AppException) as exc:
        svc.compute_series_dates(req)
    assert exc.value.code == ErrorRegistry.SERIE_003.code


# ---------------------------------------------------------------------------
# Tests d'intégration — preview et génération
# ---------------------------------------------------------------------------


def test_preview_series_no_conflits(session: Session, test_ministere, test_campus):
    """Aucun planning existant → conflits vides. Jan 7 est un lundi en 2030."""
    svc = SerieService(db=session)
    req = GenerateSeriesPreviewRequest(
        date_debut=date(2030, 1, 7),
        date_fin=date(2030, 1, 28),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=0,
    )
    result = svc.get_series_preview(req, ministere_id=test_ministere.id)
    assert result.total == 4
    assert result.conflits == []


def test_preview_series_with_conflits(session: Session, test_ministere, test_campus):
    """Planning existant sur une date → dans conflits[]."""
    target = date(2031, 2, 3)
    debut = datetime(target.year, target.month, target.day, 9, 0)
    fin = debut + timedelta(hours=2)
    activite = Activite(
        type="Culte",
        date_debut=debut,
        date_fin=fin,
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(activite)
    session.flush()
    planning = PlanningService(activite_id=activite.id, statut_code="BROUILLON")
    session.add(planning)
    session.flush()

    svc = SerieService(db=session)
    req = GenerateSeriesPreviewRequest(
        date_debut=target,
        date_fin=target,
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=target.weekday(),
    )
    result = svc.get_series_preview(req, ministere_id=test_ministere.id)
    assert len(result.conflits) == 1
    assert result.conflits[0].planning_id == planning.id


def test_generate_series_creates_plannings(
    session: Session,
    test_ministere,
    test_campus,
    test_membre,
    template_serie,
):
    """N plannings créés en DB, tous BROUILLON, même serie_id.

    2032-03-04 est un jeudi (weekday=3) → 4 jeudis jusqu'au 25/03.
    """
    svc = SerieService(db=session)
    req = GenerateSeriesRequest(
        date_debut=date(2032, 3, 4),
        date_fin=date(2032, 3, 25),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=3,
        template_id=template_serie.id,
    )
    result = svc.generate_series(
        req,
        created_by_id=test_membre.id,
        ministere_id=test_ministere.id,
        campus_id=test_campus.id,
    )
    assert result.total == 4
    assert len(result.plannings) == 4
    for item in result.plannings:
        p = session.get(PlanningService, item.id)
        assert p is not None
        assert p.statut_code == "BROUILLON"
        assert p.serie_id == result.serie_id


def test_generate_series_apply_template(
    session: Session,
    test_ministere,
    test_campus,
    test_membre,
    template_serie_avec_membre,
):
    """Créneaux créés sur chaque planning de la série.

    2033-04-07 est un jeudi (weekday=3) → 2 jeudis jusqu'au 14/04.
    """
    svc = SerieService(db=session)
    req = GenerateSeriesRequest(
        date_debut=date(2033, 4, 7),
        date_fin=date(2033, 4, 14),
        recurrence=SerieRecurrence.HEBDOMADAIRE,
        jour_semaine=3,
        template_id=template_serie_avec_membre.id,
    )
    result = svc.generate_series(
        req,
        created_by_id=test_membre.id,
        ministere_id=test_ministere.id,
        campus_id=test_campus.id,
    )
    assert result.total == 2
    for item in result.plannings:
        p = session.get(PlanningService, item.id)
        assert p is not None


# ---------------------------------------------------------------------------
# Test API — droits
# ---------------------------------------------------------------------------


def test_api_preview_series_forbidden_no_auth(client):
    """Sans token → 401 sur preview-series."""
    resp = client.post(
        "/planning-templates/preview-series",
        json={
            "date_debut": "2030-01-06",
            "date_fin": "2030-01-27",
            "recurrence": "HEBDOMADAIRE",
            "jour_semaine": 0,
        },
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
