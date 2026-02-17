from uuid import uuid4

import pytest
from fastapi import status
from models import Campus, Ministere
from sqlmodel import Session

# pylint: disable=redefined-outer-name, unused-argument

# --- FIXTURES DE STRUCTURE ---


@pytest.fixture
def test_min(session: Session, test_campus: Campus) -> Ministere:
    minis = Ministere(
        nom=f"Ministere Initial {uuid4()}",
        campus_id=test_campus.id,
        date_creation="2024-01-01",
    )
    session.add(minis)
    session.flush()
    session.refresh(minis)
    return minis


# --- TESTS CRUD & CAS CRITIQUES ---


def test_create_ministere_success(client, admin_headers, test_campus):
    """Vérifie la création réussie avec campus valide."""
    payload = {
        "nom": f"Ministère Louange {uuid4()}",
        "date_creation": "2024-01-01",
        "campus_id": test_campus.id,
    }
    response = client.post("/ministeres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == payload["nom"]
    assert "id" in data
    assert "poles_count" in data  # Vérifie que le computed field est présent


def test_create_ministere_duplicate_name(client, admin_headers, test_min):
    """Vérifie qu'on ne peut pas avoir deux ministères
    avec le même nom sur le même campus."""
    payload = {
        "nom": test_min.nom,
        "date_creation": "2024-01-01",
        "campus_id": test_min.campus_id,
    }
    response = client.post("/ministeres/", json=payload, headers=admin_headers)
    # Ton service lève une BadRequestException sur IntegrityError
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_ministere_orphaned_fails(client, admin_headers):
    """Vérifie le 404 si le campus_id n'existe pas."""
    payload = {
        "nom": "Ministere Sans Campus",
        "date_creation": "2024-01-01",
        "campus_id": str(uuid4()),
    }
    response = client.post("/ministeres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_ministeres_pagination(client, test_min):
    """Vérifie la liste paginée (public)."""
    response = client.get("/ministeres/?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) >= 1


def test_get_one_ministere_with_counts(client, test_min):
    """Vérifie la lecture d'un ministère unique et ses compteurs."""
    response = client.get(f"/ministeres/{test_min.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_min.id
    assert "poles_count" in data
    assert isinstance(data["poles_count"], int)


def test_update_ministere_partial(client, admin_headers, test_min):
    """Vérifie la mise à jour partielle (PATCH)."""
    new_nom = f"Nom Modifié {uuid4()}"
    payload = {"nom": new_nom}
    response = client.patch(
        f"/ministeres/{test_min.id}", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == new_nom
    # Vérifie que les autres champs n'ont pas bougé
    assert response.json()["date_creation"] == test_min.date_creation


def test_update_ministere_invalid_name(client, admin_headers, test_min):
    """Vérifie la validation Pydantic (pas de nom vide)."""
    payload = {"nom": "   "}
    response = client.patch(
        f"/ministeres/{test_min.id}", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_delete_ministere_as_admin(client, admin_headers, test_min, session):
    response = client.delete(f"/ministeres/{test_min.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # On rafraîchit l'état local
    session.expire_all()

    # Vérification 1 : L'API doit retourner 404 (car le repo filtre deleted_at IS NULL)
    get_resp = client.get(f"/ministeres/{test_min.id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    # Vérification 2 : La donnée existe en base pour le Big Data
    # On utilise session.get qui court-circuite parfois les filtres complexes
    check = session.get(Ministere, test_min.id)
    assert check is not None
    assert check.deleted_at is not None


def test_delete_ministere_security(client, user_headers, test_min):
    """Vérifie qu'un USER ne peut pas DELETE (403)."""
    response = client.delete(f"/ministeres/{test_min.id}", headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
