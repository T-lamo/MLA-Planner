# src/tests/test_choriste.py
from uuid import uuid4

import pytest
from fastapi import status

from mla_enum import VoixEnum
from models import Choriste

# pylint: disable=redefined-outer-name


# ----------------------------------------------------------------
# TESTS DE CRÉATION (CREATE)
# ----------------------------------------------------------------


def test_create_choriste_full_success(client, admin_headers, test_chantre):
    """Teste la création réussie avec une voix principale et une secondaire."""
    payload = {
        "chantre_id": str(test_chantre.id),
        "voix_assoc": [
            {"voix_code": VoixEnum.TENOR, "is_principal": True},
            {"voix_code": VoixEnum.BASSE, "is_principal": False},
        ],
    }
    response = client.post("/choristes/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["chantre_id"] == str(test_chantre.id)
    assert len(data["voix_assoc"]) == 2
    # Vérifie la présence de la voix principale via la logique Pydantic
    assert any(
        v["voix_code"] == VoixEnum.TENOR and v["is_principal"]
        for v in data["voix_assoc"]
    )


@pytest.mark.parametrize(
    "voix_payload, error_msg",
    [
        ([], "au moins une voix"),
        (
            [{"voix_code": VoixEnum.TENOR, "is_principal": False}],
            "exactement une voix principale",
        ),
        (
            [
                {"voix_code": VoixEnum.TENOR, "is_principal": True},
                {"voix_code": VoixEnum.ALTO, "is_principal": True},
            ],
            "plusieurs voix principales",
        ),
    ],
)
def test_create_choriste_business_validation(
    client, admin_headers, test_chantre, voix_payload, error_msg
):
    """Vérifie que les règles métier sur la voix principale sont respectées (422)."""
    payload = {"chantre_id": str(test_chantre.id), "voix_assoc": voix_payload}
    response = client.post("/choristes/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error_msg in response.text


# ----------------------------------------------------------------
# TESTS DE LECTURE (READ)
# ----------------------------------------------------------------


def test_get_choriste_by_id_with_voix(client, admin_headers, test_choriste):
    """Vérifie qu'on récupère bien un choriste et ses voix associées."""
    response = client.get(f"/choristes/{test_choriste.id}", headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_choriste.id)
    assert data["voix_assoc"][0]["voix_code"] == VoixEnum.SOPRANO


def test_list_all_choristes_paginated(client, admin_headers, test_choriste):
    """Vérifie la pagination et la présence de données dans la liste."""
    response = client.get("/choristes/?limit=10&offset=0", headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    assert any(str(test_choriste.id) == item["id"] for item in data["data"])


# ----------------------------------------------------------------
# TESTS DE MISE À JOUR (UPDATE)
# ----------------------------------------------------------------


def test_update_choriste_change_voix(client, admin_headers, test_choriste):
    """Teste le remplacement complet des voix d'un choriste."""
    payload = {"voix_assoc": [{"voix_code": VoixEnum.ALTO, "is_principal": True}]}
    response = client.patch(
        f"/choristes/{test_choriste.id}", json=payload, headers=admin_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["voix_assoc"]) == 1
    assert data["voix_assoc"][0]["voix_code"] == VoixEnum.ALTO


def test_update_choriste_invalid_principal(client, admin_headers, test_choriste):
    """Vérifie que l'update rejette une liste de voix sans principale."""
    payload = {"voix_assoc": [{"voix_code": VoixEnum.ALTO, "is_principal": False}]}
    response = client.patch(
        f"/choristes/{test_choriste.id}", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ----------------------------------------------------------------
# TESTS DE SUPPRESSION (DELETE)
# ----------------------------------------------------------------


def test_delete_choriste_soft(client, admin_headers, test_choriste, session):
    """Vérifie que la suppression marque le choriste comme supprimé (Soft Delete)."""
    response = client.delete(f"/choristes/{test_choriste.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Synchronisation avec la DB
    session.expire_all()
    db_obj = session.get(Choriste, test_choriste.id)

    # On vérifie si deleted_at est rempli (si ton service implémente le soft delete)
    assert db_obj.deleted_at is not None


def test_delete_non_existent_choriste(client, admin_headers):
    """Vérifie qu'on reçoit un 404 sur un ID inconnu."""
    response = client.delete(f"/choristes/{uuid4()}", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
