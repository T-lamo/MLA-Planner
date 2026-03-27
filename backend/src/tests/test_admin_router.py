"""Tests pour admin_router — CRUD rôles.

Note : les capabilities sont définies statiquement dans data.py et seedées
au bootstrap. Les endpoints POST/DELETE /capabilities ont été supprimés.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models.schema_db_model import AffectationRole, Role

# pylint: disable=redefined-outer-name


# ------------------------------------------------------------------ #
#  FIXTURES
# ------------------------------------------------------------------ #


@pytest.fixture
def admin_client(client: TestClient, test_superadmin, session: Session):
    """Client authentifié en tant qu'admin."""
    return client


@pytest.fixture
def free_role(session: Session) -> Role:
    """Rôle sans affectations ni permissions pour les tests de suppression."""
    role = session.exec(select(Role).where(Role.libelle == "Role Test Libre")).first()
    if not role:
        role = Role(libelle="Role Test Libre")
        session.add(role)
        session.flush()
        session.refresh(role)
    return role


@pytest.fixture
def used_role(session: Session) -> Role:
    """Rôle avec une affectation active (non supprimable)."""
    role = session.exec(select(Role).where(Role.libelle == "Role Utilise")).first()
    if not role:
        role = Role(libelle="Role Utilise")
        session.add(role)
        session.flush()
        session.refresh(role)
    return role


# ------------------------------------------------------------------ #
#  GET /admin/capabilities
# ------------------------------------------------------------------ #


def test_list_capabilities_requires_auth(client: TestClient):
    resp = client.get("/admin/capabilities")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_capabilities_ok(admin_client: TestClient, superadmin_headers: dict):
    resp = admin_client.get("/admin/capabilities", headers=superadmin_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)


# ------------------------------------------------------------------ #
#  GET /admin/roles
# ------------------------------------------------------------------ #


def test_list_roles_ok(admin_client: TestClient, superadmin_headers: dict):
    resp = admin_client.get("/admin/roles", headers=superadmin_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    assert all("id" in r and "permissions" in r for r in data)


# ------------------------------------------------------------------ #
#  POST /admin/roles
# ------------------------------------------------------------------ #


def test_create_role_ok(
    admin_client: TestClient, superadmin_headers: dict, session: Session
):
    resp = admin_client.post(
        "/admin/roles",
        json={"libelle": "Coordinateur Test"},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["libelle"] == "Coordinateur Test"
    assert data["permissions"] == []
    # Nettoyage
    role = session.exec(select(Role).where(Role.libelle == "Coordinateur Test")).first()
    if role:
        session.delete(role)
        session.flush()


def test_create_role_duplicate(
    admin_client: TestClient,
    superadmin_headers: dict,
    free_role: Role,
):
    resp = admin_client.post(
        "/admin/roles",
        json={"libelle": "Role Test Libre"},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_create_role_empty_libelle(admin_client: TestClient, superadmin_headers: dict):
    resp = admin_client.post(
        "/admin/roles",
        json={"libelle": "   "},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------ #
#  DELETE /admin/roles/{id}
# ------------------------------------------------------------------ #


def test_delete_role_ok(
    admin_client: TestClient,
    superadmin_headers: dict,
    free_role: Role,
):
    resp = admin_client.delete(
        f"/admin/roles/{free_role.id}",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_role_in_use(
    admin_client: TestClient,
    superadmin_headers: dict,
    used_role: Role,
    session: Session,
    test_superadmin,
):
    # Créer une affectation sur ce rôle
    aff = AffectationRole(utilisateur_id=test_superadmin.id, role_id=used_role.id)
    session.add(aff)
    session.flush()

    resp = admin_client.delete(
        f"/admin/roles/{used_role.id}",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_delete_role_not_found(admin_client: TestClient, superadmin_headers: dict):
    resp = admin_client.delete(
        "/admin/roles/nonexistent-id",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
