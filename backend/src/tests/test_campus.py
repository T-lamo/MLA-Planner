from uuid import uuid4

from fastapi import status
from fastapi.encoders import jsonable_encoder  # Import crucial

from models.campus_model import CampusRead
from models.membre_model import MembreRead

CampusRead.model_rebuild()
MembreRead.model_rebuild()

# pylint: disable=redefined-outer-name, unused-argument

# --- TESTS DE CRÉATION (POST) ---


def test_create_campus_as_superadmin(client, superadmin_headers, test_pays):
    """Vérifie la création réussie par un superadmin."""
    payload = {
        "nom": f"Campus SuperAdmin {uuid4()}",
        "ville": "Abidjan",
        "timezone": "Africa/Abidjan",
        "pays_id": test_pays.id,
    }
    response = client.post(
        "/campuses/", json=jsonable_encoder(payload), headers=superadmin_headers
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
        "/campuses/", json=jsonable_encoder(payload), headers=user_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_campus_invalid_pays(client, superadmin_headers):
    """Vérifie l'erreur 404 sur pays inexistant."""
    payload = {
        "nom": "Campus Perdu",
        "ville": "Nulle part",
        "pays_id": uuid4(),
    }
    response = client.post(
        "/campuses/", json=jsonable_encoder(payload), headers=superadmin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- TESTS DE LECTURE (GET) ---


def test_list_campus_pagination(client, test_campus):
    response = client.get("/campuses/?limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_get_one_campus(client, test_campus):
    response = client.get(f"/campuses/{test_campus.id}")
    assert response.status_code == status.HTTP_200_OK
    # CORRECTION : On compare le JSON (str) avec la version string de l'UUID
    assert response.json()["id"] == str(test_campus.id)


# --- TESTS DE MISE À JOUR (PATCH) ---


def test_update_campus_superadmin(client, superadmin_headers, test_campus):
    payload = {"nom": f"Nouveau Nom {uuid4()}"}
    response = client.patch(
        f"/campuses/{test_campus.id}", json=payload, headers=superadmin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == payload["nom"]


# --- TESTS DE SUPPRESSION (DELETE) ---


def test_delete_campus_superadmin(client, superadmin_headers, test_campus):
    response = client.delete(f"/campuses/{test_campus.id}", headers=superadmin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_campus_not_found(client, superadmin_headers):
    fake_id = uuid4()
    response = client.delete(f"/campuses/{fake_id}", headers=superadmin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- TESTS ROUTES SPÉCIFIQUES ---


def test_list_all_campuses(client, test_campus):
    """Vérifie la récupération de la liste complète sans pagination."""
    # Act
    response = client.get("/campuses/all")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert any(c["id"] == str(test_campus.id) for c in data["data"])


def test_link_ministeres_to_campus(
    client, superadmin_headers, test_campus, test_ministere
):
    """Vérifie la liaison Many-to-Many campus ↔ liste de ministères (remplace)."""
    response = client.post(
        f"/campuses/{test_campus.id}/ministeres",
        json=jsonable_encoder([str(test_ministere.id)]),
        headers=superadmin_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(m["id"] == str(test_ministere.id) for m in data.get("ministeres", []))


def test_link_ministeres_campus_not_found(client, superadmin_headers):
    """Vérifie le 404 si le campus cible n'existe pas."""
    fake_campus_id = str(uuid4())

    response = client.post(
        f"/campuses/{fake_campus_id}/ministeres",
        json=[str(uuid4())],
        headers=superadmin_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_link_ministeres_ministere_not_found(client, superadmin_headers, test_campus):
    """Vérifie le 404 si un ministère de la liste n'existe pas en base."""
    fake_ministere_id = str(uuid4())

    response = client.post(
        f"/campuses/{test_campus.id}/ministeres",
        json=[fake_ministere_id],
        headers=superadmin_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_link_ministeres_forbidden_for_user(
    client, user_headers, test_campus, test_ministere
):
    """Vérifie que seul l'admin peut lier des ministères (403 pour user)."""
    # Act
    response = client.post(
        f"/campuses/{test_campus.id}/ministeres",
        json=jsonable_encoder([str(test_ministere.id)]),
        headers=user_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_add_single_ministere_to_campus(
    client, superadmin_headers, test_campus, test_ministere
):
    """Vérifie l'ajout d'un ministère unique sans écraser les liaisons existantes."""
    response = client.patch(
        f"/campuses/{test_campus.id}/ministeres/{test_ministere.id}",
        headers=superadmin_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(m["id"] == str(test_ministere.id) for m in data.get("ministeres", []))


def test_add_single_ministere_not_found(client, superadmin_headers, test_campus):
    """Vérifie le 404 si le ministère à ajouter n'existe pas."""
    fake_ministere_id = str(uuid4())

    response = client.patch(
        f"/campuses/{test_campus.id}/ministeres/{fake_ministere_id}",
        headers=superadmin_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_campus_full_details(client, admin_headers, test_campus):
    """Vérifie la récupération du détail complet d'un campus (membres + ministères)."""
    # Act
    response = client.get(
        f"/campuses/{test_campus.id}/details",
        headers=admin_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_campus.id)
    assert "membres" in data
    assert "ministeres" in data


def test_get_campus_full_details_not_found(client, admin_headers):
    """Vérifie le 404 pour un campus inexistant."""
    # Arrange
    fake_id = str(uuid4())

    # Act
    response = client.get(
        f"/campuses/{fake_id}/details",
        headers=admin_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_campus_ministeres_detailed(
    client, admin_headers, test_campus, test_ministere
):
    """Vérifie la récupération enrichie des ministères liés à un campus."""
    # Arrange : établir la liaison via l'endpoint dédié
    client.post(
        f"/campuses/{test_campus.id}/ministeres",
        json=jsonable_encoder([str(test_ministere.id)]),
        headers=admin_headers,
    )

    # Act
    response = client.get(
        f"/campuses/{test_campus.id}/ministeres/detailed",
        headers=admin_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
