from uuid import uuid4

from fastapi import status

# pylint: disable=redefined-outer-name, unused-argument


def test_create_organisation_success(client, superadmin_headers):
    """Teste la création réussie avec les headers JWT d'un superadmin."""
    payload = {"nom": f"Eglise Test {uuid4()}", "date_creation": "2024-01-01"}

    response = client.post("/organisations/", json=payload, headers=superadmin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == payload["nom"]
    assert "id" in data


def test_create_organisation_duplicate_name(client, superadmin_headers):
    """Teste le rejet d'un nom d'organisation en double."""
    nom_unique = f"Organisation Unique {uuid4()}"
    payload = {"nom": nom_unique, "date_creation": "2024-01-01"}

    client.post("/organisations/", json=payload, headers=superadmin_headers)

    response = client.post("/organisations/", json=payload, headers=superadmin_headers)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "existe déjà" in response.json()["error"]["message"]


def test_get_organisations_pagination(client):
    """Teste la lecture publique (sans headers si ta route est ouverte)."""
    response = client.get("/organisations/?limit=5&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "data" in data
    assert isinstance(data["data"], list)


def test_delete_organisation_not_found(client, superadmin_headers):
    """Teste la suppression d'une organisation inexistante par un superadmin."""
    fake_id = str(uuid4())
    response = client.delete(f"/organisations/{fake_id}", headers=superadmin_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_security_superadmin_required(client, user_headers):
    """
    Vérifie qu'un utilisateur standard reçoit une 403
    lorsqu'il tente de créer une organisation (SUPER_ADMIN requis).
    """
    payload = {"nom": "Tentative Hack", "date_creation": "2024-01-01"}

    response = client.post("/organisations/", json=payload, headers=user_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
