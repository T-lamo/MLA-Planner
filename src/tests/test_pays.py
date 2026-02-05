from uuid import uuid4

import pytest
from fastapi import status

from models.schema_db_model import Pays

# pylint: disable=redefined-outer-name, unused-argument
# pylint: disable= too-many-arguments, too-many-positional-arguments


@pytest.fixture
def test_org(client, admin_headers):
    payload = {"nom": f"Org For Pays {uuid4()}", "date_creation": "2024-01-01"}
    response = client.post("/organisations/", json=payload, headers=admin_headers)
    return response.json()


def test_create_pays_success_and_uppercase_logic(client, admin_headers, test_org):
    payload = {
        "nom": "Côte d'Ivoire",
        "code": "ci ",  # Note l'espace et les minuscules
        "organisation_id": test_org["id"],
    }
    response = client.post("/pays/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    # Test du validator Pydantic : strip + upper
    assert data["code"] == "CI"
    assert data["nom"] == "Côte d'Ivoire"


def test_create_pays_invalid_org(client, admin_headers):
    payload = {
        "nom": "Pays Imaginaire",
        "code": "PI",
        "organisation_id": str(uuid4()),  # ID inexistant
    }
    response = client.post("/pays/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "introuvable" in response.json()["detail"]


def test_list_pays_contains_org_data(client, test_org, session):
    pays = Pays(nom="Bénin", code="BJ", organisation_id=test_org["id"])
    session.add(pays)
    session.commit()
    session.refresh(pays)
    response = client.get("/pays/")
    data = response.json()

    # Vérifications
    assert len(data["data"]) > 0, "La liste des pays est vide"

    # Vérifie qu'au moins un pays contient organisation_id correct
    assert any(
        p.get("organisation_id") == test_org["id"] for p in data["data"]
    ), f"Aucun pays retourné n'a organisation_id = {test_org['id']}"

    # Optionnel : vérifier que tous les pays ont un organisation_id
    for p in data["data"]:
        assert "organisation_id" in p, f"organisation_id manquant pour le pays {p}"
