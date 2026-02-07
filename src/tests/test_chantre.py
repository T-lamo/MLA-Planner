from fastapi import status

from mla_enum.custom_enum import NiveauChantre
from models import Chantre

# --- TESTS ---


def test_create_chantre_success(client, admin_headers, test_membre):
    payload = {
        "membre_id": str(test_membre.id),
        "niveau": NiveauChantre.AVANCE.value,
        "date_integration": "2026-02-06",
    }
    response = client.post("/chantres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["niveau"] == NiveauChantre.AVANCE.value
    # assert data["choristes_count"] == 0


def test_get_chantre_by_id(client, admin_headers, test_chantre):
    response = client.get(f"/chantres/{test_chantre.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_chantre.id)
    # assert "affectations_count" in data


def test_update_chantre(client, admin_headers, test_chantre):
    payload = {"niveau": NiveauChantre.AVANCE.value}
    response = client.patch(
        f"/chantres/{test_chantre.id}", json=payload, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["niveau"] == NiveauChantre.AVANCE.value


def test_delete_chantre_soft(client, admin_headers, test_chantre, session):
    response = client.delete(f"/chantres/{test_chantre.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérifier le Soft Delete
    session.expire_all()
    db_obj = session.get(Chantre, test_chantre.id)
    assert db_obj.deleted_at is not None
