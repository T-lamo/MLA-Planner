from datetime import datetime, timedelta

from fastapi import status

from models import Activite


def test_create_activite_success(client, activite_data, admin_headers):
    response = client.post("/activities/", json=activite_data, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["type"] == "Culte"
    assert data["lieu"] == "Auditorium Principal"


def test_create_activite_invalid_dates(client, activite_data, admin_headers):
    # Inversion des dates
    activite_data["date_fin"] = activite_data["date_debut"]
    response = client.post("/activities/", json=activite_data, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "date_fin doit être postérieure à date_debut" in response.text


def test_get_activite_not_found(client, admin_headers):
    response = client.get("/activities/non-existent-uuid", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_activite_partial(
    client, session, test_campus, test_ministere, admin_headers
):
    # Création initiale

    act = Activite(
        type="Atelier",
        date_debut=datetime.now(),
        date_fin=datetime.now() + timedelta(hours=1),
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(act)
    session.commit()
    session.refresh(act)

    update_payload = {"lieu": "Nouvelle Salle", "type": "séminaire"}
    response = client.patch(
        f"/activities/{act.id}", json=update_payload, headers=admin_headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["lieu"] == "Nouvelle Salle"
    assert response.json()["type"] == "Séminaire"  # Test du field_validator title()


def test_soft_delete_activite(
    client, session, test_campus, test_ministere, admin_headers
):
    act = Activite(
        type="Test Delete",
        date_debut=datetime.now(),
        date_fin=datetime.now() + timedelta(hours=1),
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
    )
    session.add(act)
    session.commit()

    # Delete
    response = client.delete(f"/activities/{act.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérification que le GET ne le trouve plus (grâce au filtre BaseRepository)
    response_get = client.get(f"/activities/{act.id}", headers=admin_headers)
    assert response_get.status_code == status.HTTP_404_NOT_FOUND
