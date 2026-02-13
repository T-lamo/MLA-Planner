from fastapi import status


def test_create_role_success(client, admin_headers, test_cat):
    payload = {
        "code": "PYTHON_DEV",
        "libelle": "Développeur Python",
        "categorie_code": test_cat.code,
    }
    response = client.post("/roles-competences/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "PYTHON_DEV"


def test_create_role_invalid_category(client, admin_headers):
    payload = {"code": "GHOST", "libelle": "Invalide", "categorie_code": "NON_EXISTENT"}
    response = client.post("/roles-competences/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_role_duplicate_code(client, admin_headers, test_cat):
    payload = {"code": "UNIQ", "libelle": "Unique", "categorie_code": test_cat.code}
    client.post("/roles-competences/", json=payload, headers=admin_headers)

    # Tentative de doublon
    response = client.post("/roles-competences/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_get_one_role(client, admin_headers, test_cat):
    code = "SEARCH_ME"
    client.post(
        "/roles-competences/",
        json={"code": code, "libelle": "Find", "categorie_code": test_cat.code},
        headers=admin_headers,
    )

    response = client.get(f"/roles-competences/{code}", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == code
