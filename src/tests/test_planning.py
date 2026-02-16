from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from pydantic import ValidationError
from sqlmodel import select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from mla_enum.custom_enum import PlanningStatusCode
from models import Activite, PlanningService
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

    with pytest.raises(AppException) as exc:
        svc.create_full_planning(PlanningFullCreate(**payload))
    assert exc.value.code == ErrorRegistry.ASGN_MEMBER_MISSING_ROLE.code
    assert exc.value.http_status == status.HTTP_400_BAD_REQUEST

    # VERIFICATION DE L'ATOMICITÉ
    # On vérifie qu'aucune activité n'a été persistée malgré l'étape 1 réussie
    statement = select(Activite).where(Activite.type == "Activite Fantome")
    activities = session.exec(statement).all()
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
                f"❌ {'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}"
                for error in e.errors()
            ]
        )
        pytest.fail(f"Erreur de validation Pydantic:{details}")
        return None


# --- TESTS ---


def test_create_full_planning_minimal_payload(session, test_campus, test_ministere):
    """Vérifie que le planning est créé avec le
    statut par défaut si 'planning' est None."""
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
    with pytest.raises(AppException) as exc:
        svc.create_full_planning(full_data)
    assert exc.value.code == ErrorRegistry.SLOT_COLLISION.code
    assert exc.value.http_status == status.HTTP_409_CONFLICT

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

    # On s'attend à une erreur
    # (soit ValidationError de Pydantic, soit BadRequest du service)
    with pytest.raises(AppException) as exc:
        svc.create_full_planning(PlanningFullCreate(**payload))

    assert exc.value.code == ErrorRegistry.SLOT_OUT_OF_BOUNDS.code

    # L'activité ne doit pas exister en base
    session.expire_all()
    # Recherche par le type unique généré
    statement = select(Activite).where(Activite.type == unique_type)
    db_act = session.exec(statement).first()
    assert db_act is None, "L'activité n'aurait pas dû être persistée"


def test_api_delete_full_planning_success(
    client, admin_headers, session, robust_data_factory
):
    """
    Test d'intégration : Vérifie que l'appel API supprime tout correctement.
    """
    # 1. GIVEN : Un arbre complet en base (BROUILLON)
    planning = robust_data_factory(status=PlanningStatusCode.BROUILLON.value)
    planning_id = str(planning.id)
    activite_id = str(planning.activite_id)

    # On commit pour que la session de l'API voit les données
    session.commit()

    # 2. WHEN : Appel DELETE
    response = client.delete(f"/plannings/{planning_id}/full", headers=admin_headers)

    # 3. THEN : 204 et vérification DB
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # On rafraîchit la session de test pour vérifier la DB réelle
    session.expire_all()
    assert session.get(PlanningService, planning_id) is None
    assert session.get(Activite, activite_id) is None


def test_api_delete_full_planning_forbidden_if_published(
    client, admin_headers, session, robust_data_factory
):
    """
    Vérifie que l'API renvoie 400 si on tente de supprimer un planning PUBLIE.
    """
    # 1. GIVEN : Un planning déjà publié
    planning = robust_data_factory(status=PlanningStatusCode.PUBLIE.value)
    session.commit()

    # 2. WHEN
    response = client.delete(f"/plannings/{planning.id}/full", headers=admin_headers)

    # 3. THEN : 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["error"]["code"]
        == ErrorRegistry.PLANNING_DELETE_IMPOSSIBLE.code
    )
    assert (
        response.json()["error"]["status"]
        == ErrorRegistry.PLANNING_DELETE_IMPOSSIBLE.http_status
    )


def test_api_delete_full_planning_not_found(client, admin_headers):
    """
    Vérifie le retour 404 pour un ID inexistant.
    """
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/plannings/{fake_id}/full", headers=admin_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
