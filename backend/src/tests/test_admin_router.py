"""Tests pour admin_router — CRUD rôles et capabilities."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models.schema_db_model import AffectationRole, Permission, Role, RolePermission

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


@pytest.fixture
def free_capability(session: Session) -> Permission:
    """Capability sans rôle associé."""
    perm = session.exec(
        select(Permission).where(Permission.code == "TEST_FREE")
    ).first()
    if not perm:
        perm = Permission(code="TEST_FREE")
        session.add(perm)
        session.flush()
        session.refresh(perm)
    return perm


@pytest.fixture
def used_capability(session: Session) -> Permission:
    """Capability attachée à un rôle (non supprimable)."""
    perm = session.exec(
        select(Permission).where(Permission.code == "TEST_USED")
    ).first()
    if not perm:
        perm = Permission(code="TEST_USED")
        session.add(perm)
        session.flush()
        session.refresh(perm)
    # Rattacher à un rôle existant ou au used_role
    role = session.exec(select(Role).where(Role.libelle == "Super Admin")).first()
    if role:
        link = session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id,
            )
        ).first()
        if not link:
            session.add(RolePermission(role_id=role.id, permission_id=perm.id))
            session.flush()
    return perm


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
#  POST /admin/capabilities
# ------------------------------------------------------------------ #


def test_create_capability_ok(
    admin_client: TestClient, superadmin_headers: dict, session: Session
):
    resp = admin_client.post(
        "/admin/capabilities",
        json={"code": "MEDIA_WRITE", "description": "Gestion médias"},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["code"] == "MEDIA_WRITE"
    assert "id" in data
    # Nettoyage
    perm = session.exec(
        select(Permission).where(Permission.code == "MEDIA_WRITE")
    ).first()
    if perm:
        session.delete(perm)
        session.flush()


def test_create_capability_duplicate(
    admin_client: TestClient,
    superadmin_headers: dict,
    free_capability: Permission,
):
    resp = admin_client.post(
        "/admin/capabilities",
        json={"code": "TEST_FREE"},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_create_capability_invalid_convention(
    admin_client: TestClient, superadmin_headers: dict
):
    """Code sans underscore → validation Pydantic → 422."""
    resp = admin_client.post(
        "/admin/capabilities",
        json={"code": "NOUNDERSCORE"},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_capability_empty_code(
    admin_client: TestClient, superadmin_headers: dict
):
    resp = admin_client.post(
        "/admin/capabilities",
        json={"code": ""},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------ #
#  DELETE /admin/capabilities/{id}
# ------------------------------------------------------------------ #


def test_delete_capability_ok(
    admin_client: TestClient,
    superadmin_headers: dict,
    free_capability: Permission,
):
    resp = admin_client.delete(
        f"/admin/capabilities/{free_capability.id}",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_capability_in_use(
    admin_client: TestClient,
    superadmin_headers: dict,
    used_capability: Permission,
):
    resp = admin_client.delete(
        f"/admin/capabilities/{used_capability.id}",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_delete_capability_not_found(
    admin_client: TestClient, superadmin_headers: dict
):
    resp = admin_client.delete(
        "/admin/capabilities/nonexistent-id",
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


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
