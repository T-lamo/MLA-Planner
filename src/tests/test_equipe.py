from uuid import uuid4

import pytest
from fastapi import status

from models import EquipeMembre

# pylint: disable=redefined-outer-name


@pytest.fixture
def created_equipe(client, admin_headers, test_ministere):
    """Fixture pour avoir une équipe propre à chaque test."""
    payload = {"nom": "Team Test", "ministere_id": test_ministere.id}
    response = client.post("/equipes/", json=payload, headers=admin_headers)
    return response.json()


# --- 1. TESTS CRUD NOMINAUX ---


def test_create_equipe_success(client, admin_headers, test_ministere):
    payload = {"nom": "  Squad Tech  ", "ministere_id": test_ministere.id}
    response = client.post("/equipes/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "Squad Tech"  # Vérifie le strip() du validator
    assert data["ministere_id"] == test_ministere.id


def test_list_equipes_paginated(client, admin_headers, created_equipe):
    response = client.get("/equipes/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    # Logger le contenu de la réponse si le test échoue
    equipe_ids = [equipe_ids["id"] for equipe_ids in data["data"]]
    assert str(created_equipe["id"]) in equipe_ids


# --- 2. TESTS DE RELATION (MANY-TO-MANY) ---


def test_add_membre_to_equipe_success(
    client, admin_headers, created_equipe, test_membre
):
    equipe_id = created_equipe["id"]
    membre_id = test_membre.id

    response = client.post(
        f"/equipes/{equipe_id}/membres/{membre_id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Vérification du chargement via get_by_id (qui load default_relations)
    get_res = client.get(f"/equipes/{equipe_id}", headers=admin_headers)
    # Si ton schéma EquipeRead incluait les membres, on vérifierait ici.
    # Sinon, on vérifie l'existence en base via la session si nécessaire.
    assert get_res.status_code == status.HTTP_200_OK


def test_remove_membre_from_equipe(
    client, admin_headers, created_equipe, test_membre, session
):
    equipe_id = created_equipe["id"]
    membre_id = test_membre.id

    # Setup : ajout préalable
    client.post(f"/equipes/{equipe_id}/membres/{membre_id}", headers=admin_headers)

    # Action : suppression
    response = client.delete(
        f"/equipes/{equipe_id}/membres/{membre_id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérification base : le lien doit avoir disparu
    link = session.get(EquipeMembre, (equipe_id, membre_id))
    assert link is None


# --- 3. TESTS D'ERREURS ET CAS LIMITES ---


def test_create_equipe_empty_name(client, admin_headers, test_ministere):
    payload = {"nom": "   ", "ministere_id": test_ministere.id}
    response = client.post("/equipes/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_add_member_already_present(client, admin_headers, created_equipe, test_membre):
    equipe_id = created_equipe["id"]
    membre_id = test_membre.id

    # Premier ajout
    client.post(f"/equipes/{equipe_id}/membres/{membre_id}", headers=admin_headers)

    # Deuxième ajout (Conflit)
    response = client.post(
        f"/equipes/{equipe_id}/membres/{membre_id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "déjà dans cette équipe" in response.json()["detail"]


def test_add_member_to_non_existent_equipe(client, admin_headers, test_membre):
    fake_id = str(uuid4())
    response = client.post(
        f"/equipes/{fake_id}/membres/{test_membre.id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_member_not_in_equipe(
    client, admin_headers, created_equipe, test_membre
):
    equipe_id = created_equipe["id"]
    # On n'ajoute pas le membre
    response = client.delete(
        f"/equipes/{equipe_id}/membres/{test_membre.id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- 4. TEST DE SÉCURITÉ ---


def test_create_equipe_unauthorized(client, user_headers, test_ministere):
    # Un simple utilisateur ne doit pas pouvoir créer d'équipe
    payload = {"nom": "Pirate Team", "ministere_id": test_ministere.id}
    response = client.post("/equipes/", json=payload, headers=user_headers)
    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_401_UNAUTHORIZED,
    ]
