from fastapi import status


def test_create_categorie_role_nominal(client, admin_headers):
    """Cas nominal : Création d'une catégorie."""
    payload = {"code": "ADMIN_TEST", "libelle": "Administrateurs de test"}
    response = client.post("/categories-roles/", json=payload, headers=admin_headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "ADMIN_TEST"


def test_create_categorie_role_duplicate(client, admin_headers):
    """Sécurité : Empêcher le duplicata de clé primaire."""
    payload = {"code": "DUPLICATE", "libelle": "Premier"}
    client.post("/categories-roles/", json=payload, headers=admin_headers)

    response = client.post("/categories-roles/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_validate_code_security(client, admin_headers):
    """Sécurité : Vérifier que le validateur alphanumérique rejette les injections."""
    payload = {"code": "INJECT;DROP", "libelle": "Malicious"}
    response = client.post("/categories-roles/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_categorie_role_not_found(client, admin_headers):
    """Erreur : 404 sur ressource inexistante."""
    response = client.get("/categories-roles/NON_EXISTENT", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_categorie_role(client, admin_headers):
    """Cas nominal : Mise à jour du libellé."""
    code = "UPDATE_ME"
    client.post(
        "/categories-roles/",
        json={"code": code, "libelle": "Old"},
        headers=admin_headers,
    )

    response = client.patch(
        f"/categories-roles/{code}", json={"libelle": "New"}, headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["libelle"] == "New"
