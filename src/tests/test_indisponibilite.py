from fastapi import status


def test_create_indisponibilite_success(client, admin_headers, test_membre):
    payload = {
        "date_debut": "2026-05-01",
        "date_fin": "2026-05-10",
        "motif": "Vacances",
        "membre_id": test_membre.id,
    }
    response = client.post("/indisponibilites/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["motif"] == "Vacances"


def test_create_indisponibilite_invalid_dates(client, admin_headers, test_membre):
    # Cas limite : date de fin avant date de début
    payload = {
        "date_debut": "2026-05-10",
        "date_fin": "2026-05-01",
        "membre_id": test_membre.id,
    }
    response = client.post("/indisponibilites/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_indisponibilite_membre_not_found(client, admin_headers):
    # Sécurité : membre inexistant
    payload = {
        "date_debut": "2026-05-01",
        "date_fin": "2026-05-10",
        "membre_id": "non-existent-uuid",
    }
    response = client.post("/indisponibilites/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_indisponibilite_not_found(client, admin_headers):
    response = client.get("/indisponibilites/uuid-imaginaire", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
