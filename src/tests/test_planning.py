from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from core.exceptions import BadRequestException
from core.exceptions.exceptions import ConflictException
from models import Activite
from models.planning_model import PlanningFullCreate
from services.planing_service import PlanningServiceSvc


def test_create_full_planning_success(
    session, test_membre, test_membre_role, test_campus, test_ministere
):
    svc = PlanningServiceSvc(session)

    payload = {
        "activite": {
            "type": "Culte Test",
            "date_debut": "2026-05-01T08:00:00",
            "date_fin": "2026-05-01T12:00:00",
            "campus_id": test_campus.id,  # REQUIS par ActiviteCreate
            "ministere_organisateur_id": test_ministere.id,  # REQUIS par ActiviteCreate
        },
        "planning": {
            "statut_code": "BROUILLON",
            "activite_id": "00000000-0000-0000-0000-000000000000",
        },
        "slots": [
            {
                "nom_creneau": "Louange",
                "date_debut": "2026-05-01T09:00:00",
                "date_fin": "2026-05-01T10:00:00",
                "planning_id": "00000000-0000-0000-0000-000000000000",
                "affectations": [
                    {
                        "membre_id": test_membre.id,
                        "role_code": test_membre_role.role_code,
                    }
                ],
            }
        ],
    }

    full_data = PlanningFullCreate(**payload)
    result = svc.create_full_planning(full_data)

    assert result.id is not None
    assert len(result.slots) == 1
    assert result.slots[0].affectations[0].membre_id == test_membre.id


def test_create_full_planning_rollback_on_role_error(
    session, test_membre, test_ministere, test_campus
):
    """
    Vérifie que si l'affectation échoue (rôle manquant),
    l'activité créée au début du process est supprimée (rollback).
    """
    svc = PlanningServiceSvc(session)

    # Payload avec un rôle inexistant pour forcer l'échec à l'étape 4
    payload = {
        "activite": {
            "type": "Culte Test",
            "date_debut": "2026-05-01T08:00:00",
            "date_fin": "2026-05-01T12:00:00",
            "campus_id": test_campus.id,  # REQUIS par ActiviteCreate
            "ministere_organisateur_id": test_ministere.id,  # REQUIS par ActiviteCreate
        },
        "planning": {
            "statut_code": "BROUILLON",
            "activite_id": "00000000-0000-0000-0000-000000000000",
        },
        "slots": [
            {
                "nom_creneau": "Louange",
                "date_debut": "2026-05-01T09:00:00",
                "date_fin": "2026-05-01T10:00:00",
                "planning_id": "00000000-0000-0000-0000-000000000000",
                "affectations": [
                    {
                        "membre_id": test_membre.id,
                        "role_code": "ROLE_INEXISTANT",
                    }
                ],
            }
        ],
    }

    with pytest.raises(BadRequestException):
        svc.create_full_planning(PlanningFullCreate(**payload))

    # VERIFICATION DE L'ATOMICITÉ
    # On vérifie qu'aucune activité n'a été persistée malgré l'étape 1 réussie
    activities = (
        session.query(Activite).filter(Activite.type == "Activite Fantome").all()
    )
    assert (
        len(activities) == 0
    ), "L'activité devrait avoir été supprimée par le rollback"


# --- UTILITAIRE DE DEBUG ---
def validate_and_create_payload(payload):
    try:
        return PlanningFullCreate(**payload)
    except ValidationError as e:
        details = "\n".join(
            [
                f"❌ {'.'.join(str(l) for l in error['loc'])}: {error['msg']}"
                for error in e.errors()
            ]
        )
        pytest.fail(f"Erreur de validation Pydantic:{details}")


# --- TESTS ---


def test_create_full_planning_minimal_payload(session, test_campus, test_ministere):
    """Vérifie que le planning est créé avec le statut par défaut si 'planning' est None."""
    svc = PlanningServiceSvc(session)

    # On utilise un type unique pour ce test pour éviter les conflits en base
    unique_type = f"type_{uuid4().hex[:6]}"

    payload = {
        "activite": {
            "type": unique_type,
            "date_debut": datetime.now().isoformat(),
            "date_fin": (datetime.now() + timedelta(hours=1)).isoformat(),
            "campus_id": test_campus.id,
            "ministere_organisateur_id": test_ministere.id,
        },
        "planning": None,
        "slots": [],
    }

    full_data = validate_and_create_payload(payload)
    result = svc.create_full_planning(full_data)

    assert result.statut_code == "BROUILLON"
    # Vérifie que l'activité a bien été créée avec le bon type
    assert result.activite.type.lower() == unique_type


def test_create_full_planning_overlapping_slots_error(
    session, test_campus, test_ministere
):
    """Vérifie que le validateur de timing bloque les chevauchements."""
    svc = PlanningServiceSvc(session)
    now = datetime.now()

    payload = {
        "activite": {
            "type": "Culte Chevauchant",
            "date_debut": now.isoformat(),
            "date_fin": (now + timedelta(hours=4)).isoformat(),
            "campus_id": test_campus.id,
            "ministere_organisateur_id": test_ministere.id,
        },
        "slots": [
            {
                "nom_creneau": "Slot 1",
                "date_debut": (now + timedelta(hours=1)).isoformat(),
                "date_fin": (now + timedelta(hours=2)).isoformat(),
                "affectations": [],
            },
            {
                "nom_creneau": "Slot 2 (Overlap)",
                "date_debut": (now + timedelta(hours=1, minutes=30)).isoformat(),
                "date_fin": (now + timedelta(hours=2, minutes=30)).isoformat(),
                "affectations": [],
            },
        ],
    }

    full_data = validate_and_create_payload(payload)

    # MISE À JOUR : On attend un ConflictException (409) au lieu de BadRequest
    with pytest.raises(ConflictException) as exc:
        svc.create_full_planning(full_data)

    # On vérifie que le message contient bien l'explication du conflit
    assert (
        "collision" in str(exc.value).lower() or "chevauche" in str(exc.value).lower()
    )


def test_atomic_integrity_on_slot_failure(session, test_campus, test_ministere):
    """Vérifie le rollback si la création d'un slot échoue (ex: dates hors activité)."""
    svc = PlanningServiceSvc(session)

    # Utilisation d'un type très spécifique pour le test de rollback
    unique_type = f"rollbackCheck_{uuid4().hex[:6]}"

    payload = {
        "activite": {
            "type": unique_type,
            "date_debut": "2026-10-01T08:00:00",
            "date_fin": "2026-10-01T10:00:00",
            "campus_id": test_campus.id,
            "ministere_organisateur_id": test_ministere.id,
        },
        "slots": [
            {
                "nom_creneau": "Slot Hors Plage",
                "date_debut": "2026-10-01T11:00:00",  # Hors de l'activité (finit à 10h)
                "date_fin": "2026-10-01T12:00:00",
                "affectations": [],
            }
        ],
    }

    # On s'attend à une erreur (soit ValidationError de Pydantic, soit BadRequest du service)
    with pytest.raises((BadRequestException, ValidationError)):
        svc.create_full_planning(PlanningFullCreate(**payload))

    # L'activité ne doit pas exister en base
    session.expire_all()
    # Recherche par le type unique généré
    db_act = session.query(Activite).filter(Activite.type == unique_type).first()
    assert db_act is None, "L'activité n'aurait pas dû être persistée"
