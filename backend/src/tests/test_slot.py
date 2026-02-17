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


def test_create_slot_collision(session, test_planning, test_slot):
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    # On cale le slot en base
    test_slot.date_debut = activity.date_debut + timedelta(minutes=10)
    test_slot.date_fin = activity.date_debut + timedelta(minutes=50)
    session.add(test_slot)
    session.flush()

    # Tentative de création en collision
    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Slot en collision",
        date_debut=test_slot.date_debut,
        date_fin=test_slot.date_fin,
    )

    with pytest.raises(AppException) as excinfo:
        service.create_slot(data)

    # Vérification du statut HTTP 409 et du code métier
    assert excinfo.value.http_status == 409
    assert excinfo.value.code == ErrorRegistry.SLOT_COLLISION.code
    assert "Collision" in excinfo.value.message


def test_create_slot_overlap_start(session, test_planning, test_slot):
    """Nouveau slot commence pendant un slot existant."""
    service = PlanningServiceSvc(session)
    activity = test_planning.activite

    test_slot.date_debut = activity.date_debut
    test_slot.date_fin = activity.date_debut + timedelta(minutes=60)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Collision Start",
        date_debut=activity.date_debut + timedelta(minutes=30),
        date_fin=activity.date_debut + timedelta(minutes=90),
    )

    with pytest.raises(AppException) as excinfo:
        service.create_slot(data)

    assert excinfo.value.code == ErrorRegistry.SLOT_COLLISION.code


def test_create_slot_overlap_end(session, test_planning, test_slot):
    """Nouveau slot commence avant et finit pendant un slot existant."""
    service = PlanningServiceSvc(session)

    test_slot.date_debut = test_planning.activite.date_debut + timedelta(hours=1)
    test_slot.date_fin = test_slot.date_debut + timedelta(hours=1)
    session.add(test_slot)
    session.flush()

    data = SlotCreate(
        planning_id=test_planning.id,
        nom_creneau="Collision End",
        date_debut=test_slot.date_debut - timedelta(minutes=30),
        date_fin=test_slot.date_debut + timedelta(minutes=30),
    )

    with pytest.raises(AppException) as excinfo:
        service.create_slot(data)

    assert excinfo.value.code == ErrorRegistry.SLOT_COLLISION.code


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
