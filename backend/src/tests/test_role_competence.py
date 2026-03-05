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


def test_list_all_roles(client, admin_headers, test_role_comp):
    """Vérifie que GET /all retourne tous les rôles sans pagination."""
    # Act
    response = client.get("/roles-competences/all", headers=admin_headers)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert any(r["code"] == test_role_comp.code for r in data["data"])


def test_get_roles_grouped_by_category(client, admin_headers, test_cat, test_role_comp):
    """Vérifie le groupement par catégorie et l'absence d'erreur runtime
    liée au cast(Any, ...) sur la relation SQLAlchemy dans get_all_with_categories."""
    # Act
    response = client.get("/roles-competences/by-category/full", headers=admin_headers)

    # Assert : status et structure
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data

    # La réponse est une liste d'objets {categorie_libelle, roles: [...]}
    categories = data["data"]
    assert isinstance(categories, list)

    # Trouver l'entrée correspondant à la catégorie de test
    cat_entry = next(
        (c for c in categories if c.get("categorie_libelle") == test_cat.libelle),
        None,
    )
    assert cat_entry is not None, f"{test_cat.libelle!r} absent de la réponse"
    assert any(r["code"] == test_role_comp.code for r in cat_entry["roles"])


def test_get_roles_grouped_empty_db(client, admin_headers):
    """Vérifie que l'endpoint répond 200 même sans aucun rôle en base."""
    # Act (session propre sans rôle créé)
    response = client.get("/roles-competences/by-category/full", headers=admin_headers)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()
