from datetime import datetime
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session

from models import Campus, OrganisationICC, Pays

# pylint: disable=redefined-outer-name, unused-argument

# --- FIXTURES DE STRUCTURE ---


@pytest.fixture
def test_org(session: Session) -> OrganisationICC:
    """Crée une organisation avec les champs obligatoires (Inspiré de test réussi)."""
    unique_nom = f"Eglise Test {uuid4()}"
    org = OrganisationICC(
        nom=unique_nom,
        code=str(uuid4())[:5],
        date_creation=datetime.now(),  # Ou "2024-01-01"
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@pytest.fixture
def test_pays(session: Session, test_org: OrganisationICC) -> Pays:
    """Crée un pays rattaché à l'organisation."""
    pays = Pays(
        nom=f"Pays {uuid4()}",
        code=str(uuid4())[:2].upper(),
        organisation_id=test_org.id,
        date_creation=datetime.now(),
    )
    session.add(pays)
    session.commit()
    session.refresh(pays)
    return pays


@pytest.fixture
def test_campus(session: Session, test_pays: Pays) -> Campus:
    """Crée un campus initial."""
    campus = Campus(
        nom=f"Campus {uuid4()}",
        ville="Toulouse",
        timezone="Europe/Paris",
        pays_id=test_pays.id,
        date_creation=datetime.now(),
    )
    session.add(campus)
    session.commit()
    session.refresh(campus)
    return campus


# --- TESTS DE CRÉATION (POST) ---


def test_create_campus_as_admin(client, admin_headers, test_pays):
    """Vérifie la création réussie par un admin."""
    payload = {
        "nom": f"Campus Admin {uuid4()}",
        "ville": "Abidjan",
        "timezone": "Africa/Abidjan",
        "pays_id": test_pays.id,
    }
    # Vérifie bien que le préfixe dans CRUDRouterFactory est "/campus"
    response = client.post("/campus/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["nom"] == payload["nom"]


def test_create_campus_as_user_forbidden(client, user_headers, test_pays):
    """Vérifie la sécurité (403)."""
    payload = {"nom": "Hacker Campus", "ville": "X", "pays_id": test_pays.id}
    response = client.post("/campus/", json=payload, headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_campus_invalid_pays(client, admin_headers):
    """Vérifie l'erreur 404 sur pays inexistant."""
    payload = {
        "nom": "Campus Perdu",
        "ville": "Nulle part",
        "pays_id": str(uuid4()),  # UUID valide mais non présent en base
    }
    response = client.post("/campus/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- TESTS DE LECTURE (GET) ---


def test_list_campus_pagination(client, test_campus):
    """Inspiré de test_get_organisations_pagination."""
    response = client.get("/campus/?limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_get_one_campus(client, test_campus):
    response = client.get(f"/campus/{test_campus.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == test_campus.id


# --- TESTS DE MISE À JOUR (PATCH) ---


def test_update_campus_admin(client, admin_headers, test_campus):
    payload = {"nom": f"Nouveau Nom {uuid4()}"}
    response = client.patch(
        f"/campus/{test_campus.id}", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == payload["nom"]


# --- TESTS DE SUPPRESSION (DELETE) ---


def test_delete_campus_admin(client, admin_headers, test_campus, session):
    response = client.delete(f"/campus/{test_campus.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérification post-suppression
    assert session.get(Campus, test_campus.id) is None


def test_delete_campus_not_found(client, admin_headers):
    """Inspiré de test_delete_organisation_not_found."""
    fake_id = str(uuid4())
    response = client.delete(f"/campus/{fake_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
