from datetime import timedelta

import pytest

from core.exceptions import BadRequestException, ConflictException
from models.slot_model import SlotCreate
from services.planing_service import PlanningServiceSvc


def test_create_slot_success(session, test_planning):
    service = PlanningServiceSvc(session)
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Test Success",
        date_debut=test_planning.activite.date_debut,
        date_fin=test_planning.activite.date_debut + timedelta(hours=1),
    )
    result = service.create_slot(data)
    assert result.id is not None


def test_create_slot_out_of_bounds(session, test_planning):
    service = PlanningServiceSvc(session)
    # Date début avant l'activité
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Fail",
        date_debut=test_planning.activite.date_debut - timedelta(days=1),
        date_fin=test_planning.activite.date_fin,
    )
    with pytest.raises(BadRequestException):
        service.create_slot(data)


def test_create_slot_collision(session, test_planning, test_slot):
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    # AU LIEU DE test_slot.date_debut/fin
    #  qui sont peut-être hors limites de l'activité,
    # on modifie le test_slot existant
    # en base pour qu'il soit PARFAITEMENT dans l'activité.
    test_slot.date_debut = activity.date_debut + timedelta(minutes=10)
    test_slot.date_fin = activity.date_debut + timedelta(minutes=50)
    session.add(test_slot)
    session.commit()

    # Maintenant on crée la collision sur ce créneau Garanti "In-Bounds"
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Slot en collision",
        date_debut=test_slot.date_debut,  # Pile sur le même créneau
        date_fin=test_slot.date_fin,
    )

    with pytest.raises(ConflictException) as excinfo:
        service.create_slot(data)

    assert excinfo.value.status_code == 409
    assert "Collision" in excinfo.value.detail


def test_create_slot_overlap_start(session, test_planning, test_slot):
    """Nouveau slot commence pendant un slot
    existant et finit après (mais dans l'activité)."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    # 1. On cale test_slot : [T+0 min à T+60 min]
    test_slot.date_debut = activity.date_debut
    test_slot.date_fin = activity.date_debut + timedelta(minutes=60)
    session.add(test_slot)
    session.commit()

    # 2. Nouveau slot : [T+30 min à T+90 min]
    # (On vérifie que T+90 min < activity.date_fin qui est généralement T+120 min)
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Collision Start",
        date_debut=activity.date_debut + timedelta(minutes=30),
        date_fin=activity.date_debut + timedelta(minutes=90),
    )

    with pytest.raises(ConflictException):
        service.create_slot(data)


def test_create_slot_overlap_end(session, test_planning, test_slot):
    """Nouveau slot commence avant et finit pendant un slot existant."""
    service = PlanningServiceSvc(session)
    # test_slot : 10h00 - 11h00
    test_slot.date_debut = test_planning.activite.date_debut + timedelta(hours=1)
    test_slot.date_fin = test_slot.date_debut + timedelta(hours=1)
    session.add(test_slot)
    session.commit()

    # Nouveau slot : 09h30 - 10h30 (Collision à la fin)
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Collision End",
        date_debut=test_slot.date_debut - timedelta(minutes=30),
        date_fin=test_slot.date_debut + timedelta(minutes=30),
    )
    with pytest.raises(ConflictException):
        service.create_slot(data)


def test_create_slot_edge_to_edge_success(session, test_planning, test_slot):
    """Deux slots qui se touchent sans chevauchement : [T+0 à T+30] et [T+30 à T+60]."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    # 1. Premier slot : de 0 à 30 min
    test_slot.date_debut = activity.date_debut
    test_slot.date_fin = activity.date_debut + timedelta(minutes=30)
    session.add(test_slot)
    session.commit()

    # 2. Nouveau slot : de 30 min à 60 min (Succès car pas de chevauchement)
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Edge Success",
        date_debut=test_slot.date_fin,  # Exactement 30 min
        date_fin=activity.date_debut + timedelta(minutes=60),
    )

    result = service.create_slot(data)
    assert result.id is not None
