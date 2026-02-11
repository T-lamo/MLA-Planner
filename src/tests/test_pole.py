from uuid import uuid4

from fastapi import status

from models import Pole


def test_create_pole_as_admin(client, admin_headers, test_ministere):
    payload = {
        "nom": f"Pole {uuid4()}",
        "description": "Description test",
        "ministere_id": str(test_ministere.id),
    }
    response = client.post("/poles/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["nom"] == payload["nom"]


def test_create_pole_forbidden_for_user(client, user_headers, test_ministere):
    payload = {"nom": "Fail", "ministere_id": str(test_ministere.id)}
    response = client.post("/poles/", json=payload, headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_one_pole(client, test_pole):
    response = client.get(f"/poles/{test_pole.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(test_pole.id)


def test_update_pole_admin(client, admin_headers, test_pole):
    new_nom = "Nom Modifié"
    response = client.patch(
        f"/poles/{test_pole.id}", json={"nom": new_nom}, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == new_nom


def test_soft_delete_pole_admin(client, admin_headers, test_pole, session):
    # Action
    response = client.delete(f"/poles/{test_pole.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérification Soft Delete
    session.expire_all()
    # On utilise session.get pour bypasser le filtre global du repo si nécessaire
    check = session.get(Pole, str(test_pole.id))
    assert check is not None
    assert check.deleted_at is not None
    assert check.active is False
