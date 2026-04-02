from uuid import uuid4

from fastapi import status
from sqlmodel import Session

from models.schema_db_model import (
    CategorieRole,
    Ministere,
    MinistereRoleConfig,
    RoleCompetence,
)


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


# ------------------------------------------------------------------ #
#  RC-161 — Filtre rôles par ministère
# ------------------------------------------------------------------ #


def _create_ministere_with_role(
    session: Session,
    cat: CategorieRole,
) -> tuple:
    """Helper : ministère + rôle + lien MinistereRoleConfig."""
    ministere = Ministere(
        nom=f"Min-{uuid4().hex[:6]}",
        date_creation="2026-01-01",
        actif=True,
    )
    session.add(ministere)
    session.flush()
    session.refresh(ministere)

    role = RoleCompetence(
        code=f"RC{uuid4().hex[:6].upper()}",
        libelle="Rôle RC-161",
        categorie_code=cat.code,
    )
    session.add(role)
    session.flush()

    cfg = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(cfg)
    session.flush()
    session.refresh(role)
    return ministere, role


def test_get_roles_grouped_filtered_by_ministere(
    client, session: Session, admin_headers, test_cat: CategorieRole
):
    """Avec ministere_id, seuls les rôles activés pour ce ministère sont retournés."""
    ministere, role = _create_ministere_with_role(session, test_cat)

    url = f"/roles-competences/by-category/full?ministere_id={ministere.id}"
    response = client.get(url, headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    all_codes = [r["code"] for cat in data for r in cat["roles"]]
    assert role.code in all_codes


def test_get_roles_grouped_filter_excludes_other_ministere(
    client, session: Session, admin_headers, test_cat: CategorieRole
):
    """Les rôles d'un autre ministère sont absents du filtre."""
    min_a, role_a = _create_ministere_with_role(session, test_cat)
    _, role_b = _create_ministere_with_role(session, test_cat)

    url = f"/roles-competences/by-category/full?ministere_id={min_a.id}"
    response = client.get(url, headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    all_codes = [r["code"] for cat in data for r in cat["roles"]]
    assert role_a.code in all_codes
    assert role_b.code not in all_codes


def test_get_roles_grouped_unknown_ministere_returns_empty(client, admin_headers):
    """ministere_id inconnu → data vide (aucun rôle activé)."""
    url = f"/roles-competences/by-category/full?ministere_id={uuid4()}"
    response = client.get(url, headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []


def test_get_roles_grouped_no_filter_returns_all(
    client, session: Session, admin_headers, test_cat: CategorieRole
):
    """Sans ministere_id, tous les rôles du catalogue sont retournés."""
    _, role = _create_ministere_with_role(session, test_cat)

    response = client.get("/roles-competences/by-category/full", headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    all_codes = [r["code"] for cat in data for r in cat["roles"]]
    assert role.code in all_codes
