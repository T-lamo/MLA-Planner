from uuid import uuid4

from fastapi import status

# pylint: disable=redefined-outer-name, unused-argument

# --- FIXTURES DE STRUCTURE ---


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
    # --- AJOUT CRUCIAL ---
    # On s'assure que l'objet test_campus est connu de la session actuelle
    # et qu'il possède bien tous les attributs du modèle mis à jour.
    session.add(test_campus)
    session.refresh(test_campus)

    # Action
    response = client.delete(f"/campus/{test_campus.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_campus_not_found(client, admin_headers):
    """Inspiré de test_delete_organisation_not_found."""
    fake_id = str(uuid4())
    response = client.delete(f"/campus/{fake_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
