from uuid import uuid4

from fastapi import status
from fastapi.encoders import jsonable_encoder  # Import crucial

# pylint: disable=redefined-outer-name, unused-argument

# --- TESTS DE CRÉATION (POST) ---


def test_create_campus_as_admin(client, admin_headers, test_pays):
    """Vérifie la création réussie par un admin."""
    payload = {
        "nom": f"Campus Admin {uuid4()}",
        "ville": "Abidjan",
        "timezone": "Africa/Abidjan",
        "pays_id": test_pays.id,  # C'est un UUID
    }
    # On utilise jsonable_encoder pour transformer l'UUID en string JSON
    response = client.post(
        "/campus/", json=jsonable_encoder(payload), headers=admin_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["nom"] == payload["nom"]


def test_create_campus_as_user_forbidden(client, user_headers, test_pays):
    """Vérifie la sécurité (403)."""
    payload = {"nom": "Hacker Campus", "ville": "X", "pays_id": test_pays.id}
    # Toujours utiliser jsonable_encoder quand le payload contient un UUID
    response = client.post(
        "/campus/", json=jsonable_encoder(payload), headers=user_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_campus_invalid_pays(client, admin_headers):
    """Vérifie l'erreur 404 sur pays inexistant."""
    payload = {
        "nom": "Campus Perdu",
        "ville": "Nulle part",
        "pays_id": uuid4(),  # On passe l'objet UUID directement
    }
    response = client.post(
        "/campus/", json=jsonable_encoder(payload), headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- TESTS DE LECTURE (GET) ---


def test_list_campus_pagination(client, test_campus):
    response = client.get("/campus/?limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_get_one_campus(client, test_campus):
    response = client.get(f"/campus/{test_campus.id}")
    assert response.status_code == status.HTTP_200_OK
    # CORRECTION : On compare le JSON (str) avec la version string de l'UUID
    assert response.json()["id"] == str(test_campus.id)


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
    # Action
    response = client.delete(f"/campus/{test_campus.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_campus_not_found(client, admin_headers):
    fake_id = uuid4()  # On utilise l'objet UUID
    response = client.delete(f"/campus/{fake_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
