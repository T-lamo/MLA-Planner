from datetime import timedelta

import pytest

# Import de la nouvelle exception et du registre
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
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

    # Remplacement par AppException et vérification du code technique
    with pytest.raises(AppException) as excinfo:
        service.create_slot(data)

    assert excinfo.value.code == ErrorRegistry.SLOT_OUT_OF_BOUNDS.code


def test_create_slot_overlap_exact_same_window(session, test_planning, test_slot):
    """Deux slots avec exactement la même fenêtre horaire sont désormais autorisés."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    test_slot.date_debut = activity.date_debut + timedelta(minutes=10)
    test_slot.date_fin = activity.date_debut + timedelta(minutes=50)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Slot fenêtre identique",
        date_debut=test_slot.date_debut,
        date_fin=test_slot.date_fin,
    )
    result = service.create_slot(data)
    assert result.id is not None


def test_create_slot_overlap_start_allowed(session, test_planning, test_slot):
    """Nouveau slot commençant pendant un slot existant est autorisé."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    test_slot.date_debut = activity.date_debut
    test_slot.date_fin = activity.date_debut + timedelta(minutes=60)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Overlap Start",
        date_debut=activity.date_debut + timedelta(minutes=30),
        date_fin=activity.date_debut + timedelta(minutes=90),
    )
    result = service.create_slot(data)
    assert result.id is not None


def test_create_slot_overlap_end_allowed(session, test_planning, test_slot):
    """Nouveau slot finissant pendant un slot existant est autorisé."""
    service = PlanningServiceSvc(session)

    test_slot.date_debut = test_planning.activite.date_debut + timedelta(hours=1)
    test_slot.date_fin = test_slot.date_debut + timedelta(hours=1)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Overlap End",
        date_debut=test_slot.date_debut - timedelta(minutes=30),
        date_fin=test_slot.date_debut + timedelta(minutes=30),
    )
    result = service.create_slot(data)
    assert result.id is not None


def test_create_slot_edge_to_edge_success(session, test_planning, test_slot):
    """Succès si les slots se touchent sans chevauchement."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    test_slot.date_debut = activity.date_debut
    test_slot.date_fin = activity.date_debut + timedelta(minutes=30)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Edge Success",
        date_debut=test_slot.date_fin,
        date_fin=activity.date_debut + timedelta(minutes=60),
    )

    result = service.create_slot(data)
    assert result.id is not None


def test_create_slot_overlapping_different_ministere(session, test_planning):
    """Simule Louange (toute la durée) + Son&Scène (5 min) : overlap autorisé."""
    service = PlanningServiceSvc(session)
    base = test_planning.activite.date_debut
    activity_end = test_planning.activite.date_fin

    slot1 = service.create_slot(
        SlotCreate(
            planning_id=test_planning.id,
            nom_creneau="Louange — service complet",
            date_debut=base,
            date_fin=activity_end,
        )
    )
    assert slot1.id is not None

    slot2 = service.create_slot(
        SlotCreate(
            planning_id=test_planning.id,
            nom_creneau="Son & Scène — intervention courte",
            date_debut=activity_end - timedelta(minutes=5),
            date_fin=activity_end,
        )
    )
    assert slot2.id is not None


def test_create_slot_arbitrary_minutes(session, test_planning):
    """Les minutes libres (non multiples de 15) sont désormais acceptées."""
    service = PlanningServiceSvc(session)
    base = test_planning.activite.date_debut

    result = service.create_slot(
        SlotCreate(
            planning_id=test_planning.id,
            nom_creneau="Slot minutes libres",
            date_debut=base + timedelta(minutes=7),
            date_fin=base + timedelta(minutes=82),
        )
    )
    assert result.id is not None
