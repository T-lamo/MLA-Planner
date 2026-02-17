from uuid import uuid4

from fastapi import status

# pylint: disable=redefined-outer-name, unused-argument


def test_create_organisation_success(client, admin_headers):
    """Teste la création réussie avec les headers JWT d'un admin."""
    payload = {"nom": f"Eglise Test {uuid4()}", "date_creation": "2024-01-01"}

    # On passe admin_headers ici
    response = client.post("/organisations/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == payload["nom"]
    assert "id" in data


def test_create_organisation_duplicate_name(client, admin_headers, session):
    """Teste le rejet d'un nom d'organisation en double."""
    nom_unique = f"Organisation Unique {uuid4()}"
    payload = {"nom": nom_unique, "date_creation": "2024-01-01"}

    # Premier appel pour créer l'entrée
    client.post("/organisations/", json=payload, headers=admin_headers)

    # Deuxième appel (doublon)
    response = client.post("/organisations/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "existe déjà" in response.json()["detail"]


def test_get_organisations_pagination(client):
    """Teste la lecture publique (sans headers si ta route est ouverte)."""
    response = client.get("/organisations/?limit=5&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "data" in data
    assert isinstance(data["data"], list)


def test_delete_organisation_not_found(client, admin_headers):
    """Teste la suppression d'une organisation inexistante par un admin."""
    fake_id = str(uuid4())
    response = client.delete(f"/organisations/{fake_id}", headers=admin_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_security_admin_required(client, user_headers):
    """
    Vérifie qu'un utilisateur standard (non-admin) reçoit une 403
    lorsqu'il tente de créer une organisation.
    """
    payload = {"nom": "Tentative Hack", "date_creation": "2024-01-01"}

    # On utilise user_headers au lieu de admin_headers
    response = client.post("/organisations/", json=payload, headers=user_headers)

    # Le RoleChecker(["ADMIN"]) doit renvoyer Forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
