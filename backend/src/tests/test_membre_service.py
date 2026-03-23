from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry

# Importations des modèles et services (ajuste selon ta structure)
from models import Affectation, MemberAgendaResponse, MemberAgendaStats, Slot
from services.affectation_service import AffectationService
from services.slot_service import SlotService

# ==========================================
# 1. Tests de MembreService (Point d'entrée)
# ==========================================


def test_get_personal_agenda_success(membre_service, mock_db, mock_membre):
    # GIVEN
    # Ton service appelle self.repo.get_by_id.
    # On mocke les deux accès possibles (get ou exec) pour être blindé
    mock_db.get.return_value = mock_membre
    mock_db.exec.return_value.first.return_value = mock_membre

    membre_service.planning_svc.get_member_agenda_full = MagicMock(
        return_value=MemberAgendaResponse(
            period_start=datetime.now(),
            period_end=datetime.now() + timedelta(days=90),
            statistics=MemberAgendaStats(
                total_engagements=0, confirmed_rate=0.0, roles_distribution={}
            ),
            entries=[],
        )
    )

    # WHEN
    result = membre_service.get_personal_agenda("user-1")

    # THEN
    assert isinstance(result, MemberAgendaResponse)
    # On vérifie l'appel au repo (via db)
    assert mock_db.get.called or mock_db.exec.called


def test_get_personal_agenda_membre_not_found(membre_service):
    # GIVEN
    membre_service.repo.get_by_id = MagicMock(return_value=None)

    # WHEN / THEN
    with pytest.raises(AppException) as excinfo:
        membre_service.get_personal_agenda("unknown-id")

    assert excinfo.value.code == ErrorRegistry.MEMBRE_NOT_FOUND.code


# ==========================================
# 2. Tests de SlotService (Mapping)
# ==========================================


def test_slot_service_map_affectations():
    # GIVEN
    slot_svc = SlotService(db=None)

    # Mock d'affectation avec sa hiérarchie
    mock_aff = MagicMock(spec=Affectation)
    mock_aff.id = "aff-1"
    mock_aff.statut_affectation_code = "CONFIRME"
    mock_aff.role_code = "LOUANGE"

    # Mock Slot
    mock_slot = MagicMock(spec=Slot)
    mock_slot.nom_creneau = "Louange"
    mock_slot.date_debut = datetime(2026, 2, 16, 10, 0)
    mock_slot.date_fin = datetime(2026, 2, 16, 11, 0)

    # Mock Planning/Activite/Campus
    mock_aff.slot = mock_slot
    mock_aff.slot.planning.activite.nom = "Culte"
    mock_aff.slot.planning.activite.type = "CULTE"
    mock_aff.slot.planning.activite.lieu = "Salle 1"
    mock_aff.slot.planning.activite.campus.nom = "Campus A"

    # WHEN
    entries = slot_svc.map_affectations_to_entries([mock_aff])

    # THEN
    assert len(entries) == 1
    assert entries[0].nom_creneau == "Louange"
    assert entries[0].campus_nom == "Campus A"


# ==========================================
# 3. Tests de AffectationService (Stats)
# ==========================================


def test_affectation_service_stats_empty(mock_db):
    # GIVEN

    aff_svc = AffectationService(db=mock_db)
    # WHEN
    stats = aff_svc.get_stats_from_list([])

    # THEN
    assert stats["total"] == 0
    assert stats["rate"] == 0.0
    assert not stats["roles"]


def test_affectation_service_stats_calculations(mock_db):
    # GIVEN

    aff_svc = AffectationService(db=mock_db)

    aff1 = MagicMock(statut_affectation_code="CONFIRME", role_code="TECH")
    aff2 = MagicMock(statut_affectation_code="BROUILLON", role_code="TECH")
    aff3 = MagicMock(statut_affectation_code="CONFIRME", role_code="ACCUEIL")

    # WHEN
    stats = aff_svc.get_stats_from_list([aff1, aff2, aff3])

    # THEN
    assert stats["total"] == 3
    # 2 confirmés sur 3 = 66.67%
    assert stats["rate"] == 66.67
    assert stats["roles"]["TECH"] == 2
    assert stats["roles"]["ACCUEIL"] == 1
