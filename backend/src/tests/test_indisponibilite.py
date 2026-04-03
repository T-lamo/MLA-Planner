# tests/test_indisponibilite.py
# pylint: disable=redefined-outer-name
from uuid import uuid4

import pytest
from fastapi import status
from sqlmodel import Session

from models.schema_db_model import (
    Campus,
    Membre,
    Utilisateur,
)

# ---------------------------------------------------------------------------
# Fixture locale : membre lié à test_user
# ---------------------------------------------------------------------------


@pytest.fixture
def linked_membre(
    session: Session, test_user: Utilisateur, test_campus: Campus
) -> Membre:
    """Membre lié à test_user (Get-or-Create)."""
    if test_user.membre_id:
        existing = session.get(Membre, test_user.membre_id)
        if existing:
            return existing
    membre = Membre(
        nom="Dupont",
        prenom="Alice",
        email=f"alice.{uuid4()}@test.com",
        actif=True,
    )
    membre.campuses = [test_campus]
    session.add(membre)
    session.flush()

    test_user.membre_id = membre.id
    session.add(test_user)
    session.flush()
    # Expire pour forcer le rechargement de la relation membre depuis la DB
    session.expire(test_user)
    session.refresh(membre)
    return membre


@pytest.fixture
def linked_admin(
    session: Session, test_admin: Utilisateur, test_campus: Campus
) -> Membre:
    """Membre lié à test_admin (Get-or-Create)."""
    if test_admin.membre_id:
        existing = session.get(Membre, test_admin.membre_id)
        if existing:
            return existing
    membre = Membre(
        nom="Admin",
        prenom="Bob",
        email=f"bob.{uuid4()}@test.com",
        actif=True,
    )
    membre.campuses = [test_campus]
    session.add(membre)
    session.flush()
    test_admin.membre_id = membre.id
    session.add(test_admin)
    session.flush()
    # Expire pour forcer le rechargement de la relation membre depuis la DB
    session.expire(test_admin)
    session.refresh(membre)
    return membre


# ---------------------------------------------------------------------------
# Tests : déclaration membre
# ---------------------------------------------------------------------------


def test_membre_can_declare_indisponibilite(client, user_headers, linked_membre):
    payload = {
        "date_debut": "2026-09-01",
        "date_fin": "2026-09-05",
        "motif": "Congés",
        "membre_id": linked_membre.id,
    }
    r = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert r.status_code == status.HTTP_201_CREATED
    assert r.json()["motif"] == "Congés"
    assert r.json()["validee"] is False


def test_membre_cannot_declare_for_another(client, user_headers, test_membre):
    """Un membre ne peut pas déclarer pour un autre membre."""
    payload = {
        "date_debut": "2026-09-01",
        "date_fin": "2026-09-05",
        "membre_id": test_membre.id,  # autre membre
    }
    r = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_overlap_detection(client, user_headers, linked_membre):
    """Deux indisponibilités qui se chevauchent sont refusées."""
    payload = {
        "date_debut": "2026-10-01",
        "date_fin": "2026-10-10",
        "membre_id": linked_membre.id,
    }
    r1 = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert r1.status_code == status.HTTP_201_CREATED

    # Même période → chevauchement
    r2 = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert r2.json()["error"]["code"] == "INDISP_004"


def test_invalid_date_chronology(client, user_headers, linked_membre):
    """date_fin < date_debut → 422."""
    payload = {
        "date_debut": "2026-10-10",
        "date_fin": "2026-10-01",
        "membre_id": linked_membre.id,
    }
    r = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert r.json()["error"]["code"] == "INDISP_002"


# ---------------------------------------------------------------------------
# Tests : GET /me
# ---------------------------------------------------------------------------


def test_membre_can_list_own(client, user_headers, linked_membre):
    payload = {
        "date_debut": "2026-11-01",
        "date_fin": "2026-11-03",
        "membre_id": linked_membre.id,
    }
    client.post("/indisponibilites/", json=payload, headers=user_headers)
    r = client.get("/indisponibilites/me", headers=user_headers)
    assert r.status_code == status.HTTP_200_OK
    body = r.json()
    assert "data" in body
    assert body["total"] >= 1
    assert len(body["data"]) >= 1


# ---------------------------------------------------------------------------
# Tests : suppression membre
# ---------------------------------------------------------------------------


def test_membre_can_delete_own_unvalidated(client, user_headers, linked_membre):
    payload = {
        "date_debut": "2026-12-01",
        "date_fin": "2026-12-03",
        "membre_id": linked_membre.id,
    }
    create = client.post("/indisponibilites/", json=payload, headers=user_headers)
    assert create.status_code == status.HTTP_201_CREATED
    indisp_id = create.json()["id"]

    r = client.delete(f"/indisponibilites/{indisp_id}", headers=user_headers)
    assert r.status_code == status.HTTP_204_NO_CONTENT


def test_membre_cannot_delete_validated(
    client, user_headers, admin_headers, linked_membre
):
    payload = {
        "date_debut": "2027-01-05",
        "date_fin": "2027-01-10",
        "membre_id": linked_membre.id,
    }
    create = client.post("/indisponibilites/", json=payload, headers=user_headers)
    indisp_id = create.json()["id"]

    # Admin valide
    client.patch(
        f"/indisponibilites/{indisp_id}/valider",
        headers=admin_headers,
    )

    # Membre tente de supprimer → 409
    r = client.delete(f"/indisponibilites/{indisp_id}", headers=user_headers)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["error"]["code"] == "INDISP_003"


# ---------------------------------------------------------------------------
# Tests : admin
# ---------------------------------------------------------------------------


def test_admin_can_validate(client, admin_headers, user_headers, linked_membre):
    payload = {
        "date_debut": "2027-02-01",
        "date_fin": "2027-02-05",
        "membre_id": linked_membre.id,
    }
    create = client.post("/indisponibilites/", json=payload, headers=user_headers)
    indisp_id = create.json()["id"]

    r = client.patch(
        f"/indisponibilites/{indisp_id}/valider",
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["validee"] is True


def test_admin_cannot_validate_twice(
    client, admin_headers, user_headers, linked_membre
):
    payload = {
        "date_debut": "2027-03-01",
        "date_fin": "2027-03-03",
        "membre_id": linked_membre.id,
    }
    create = client.post("/indisponibilites/", json=payload, headers=user_headers)
    indisp_id = create.json()["id"]

    client.patch(
        f"/indisponibilites/{indisp_id}/valider",
        headers=admin_headers,
    )
    r = client.patch(
        f"/indisponibilites/{indisp_id}/valider",
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_409_CONFLICT
    assert r.json()["error"]["code"] == "INDISP_003"


def test_admin_can_list_by_campus(
    client, admin_headers, user_headers, linked_membre, test_campus
):
    payload = {
        "date_debut": "2027-04-01",
        "date_fin": "2027-04-05",
        "membre_id": linked_membre.id,
    }
    client.post("/indisponibilites/", json=payload, headers=user_headers)

    r = client.get(
        f"/indisponibilites/campus/{test_campus.id}",
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    body = r.json()
    assert "data" in body
    assert body["total"] >= 1
    assert len(body["data"]) >= 1


def test_filter_by_ministere(  # pylint: disable=too-many-positional-arguments
    client, admin_headers, user_headers, linked_membre, test_campus, test_ministere
):
    payload = {
        "date_debut": "2027-05-01",
        "date_fin": "2027-05-05",
        "membre_id": linked_membre.id,
        "ministere_id": test_ministere.id,
    }
    client.post("/indisponibilites/", json=payload, headers=user_headers)

    r = client.get(
        f"/indisponibilites/campus/{test_campus.id}",
        params={"ministere_id": test_ministere.id},
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()["data"]
    assert all(d["ministere_id"] == test_ministere.id for d in data)


def test_filter_by_date_range(
    client, admin_headers, user_headers, linked_membre, test_campus
):
    payload = {
        "date_debut": "2027-06-01",
        "date_fin": "2027-06-10",
        "membre_id": linked_membre.id,
    }
    client.post("/indisponibilites/", json=payload, headers=user_headers)

    r = client.get(
        f"/indisponibilites/campus/{test_campus.id}",
        params={"date_debut": "2027-06-01", "date_fin": "2027-06-15"},
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    assert len(r.json()["data"]) >= 1


def test_admin_delete(client, admin_headers, user_headers, linked_membre):
    payload = {
        "date_debut": "2027-07-01",
        "date_fin": "2027-07-05",
        "membre_id": linked_membre.id,
    }
    create = client.post("/indisponibilites/", json=payload, headers=user_headers)
    indisp_id = create.json()["id"]

    r = client.delete(
        f"/indisponibilites/{indisp_id}/admin",
        headers=admin_headers,
    )
    assert r.status_code == status.HTTP_204_NO_CONTENT
