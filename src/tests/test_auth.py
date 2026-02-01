from datetime import timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session

from core.auth.security import create_access_token
from core.settings import settings as stng
from mla_enum import RoleName
from models import Utilisateur

# pylint: disable=redefined-outer-name, unused-argument, too-many-arguments, too-many-positional-arguments


# --- TESTS DE CONNEXION (LOGIN) ---


@pytest.mark.parametrize(
    "username, password, expected_status",
    [
        ("active_user", "password123", status.HTTP_200_OK),
        ("active_user", "wrongpassword", status.HTTP_401_UNAUTHORIZED),
        ("nonexistent", "password123", status.HTTP_401_UNAUTHORIZED),
        ("banned_user", "password123", status.HTTP_403_FORBIDDEN),
    ],
)
def test_login_flow(
    client: TestClient, test_user, inactive_user, username, password, expected_status  # type: ignore # pylint: disable=too-many-arguments
):
    """
    Teste les différents scénarios de login.
    Note: On injecte test_user et inactive_user pour qu'ils soient présents en DB.
    """
    response = client.post(
        "/auth/token", data={"username": username, "password": password}
    )
    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_at" in data


def test_login_missing_fields(client: TestClient):
    """Vérifie que l'envoi de champs incomplets retourne une erreur 422."""
    response = client.post("/auth/token", data={"username": "only_user"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# --- TESTS DE RÉCUPÉRATION DE PROFIL (ME) ---


def test_get_me_success(client: TestClient, test_user: Utilisateur):
    """Vérifie la récupération de l'utilisateur courant avec un token valide."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/auth/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username


def test_get_me_expired_token(client: TestClient, test_user: Utilisateur):
    """Vérifie le rejet d'un token expiré."""
    token, _ = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=-1),  # Expire il y a une minute
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_invalid_signature(client: TestClient, test_user: Utilisateur):
    """Vérifie le rejet d'un token dont la signature est corrompue."""
    token, _ = create_access_token(data={"sub": test_user.username})
    bad_token = token[:-5] + "aaaaa"
    headers = {"Authorization": f"Bearer {bad_token}"}
    response = client.get("/auth/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- TESTS DE GESTION DE MOT DE PASSE ---


def test_change_password_own_account(client: TestClient, test_user: Utilisateur):
    """Un utilisateur peut changer son propre mot de passe."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"current_password": "password123", "new_password": "newsecurepassword"}

    response = client.patch(
        f"/auth/utilisateurs/{test_user.id}/password", json=payload, headers=headers
    )
    assert response.status_code == status.HTTP_200_OK


def test_change_password_invalid_length(client: TestClient, test_user: Utilisateur):
    """Vérifie les contraintes Pydantic (min_length=6)."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"current_password": "password123", "new_password": "123"}
    response = client.patch(
        f"/auth/utilisateurs/{test_user.id}/password", json=payload, headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_change_password_forbidden_for_other_user(
    client: TestClient, test_user: Utilisateur, test_admin: Utilisateur
):
    """Un utilisateur non-admin ne peut pas changer le mot de passe d'un tiers."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"current_password": "adminpass", "new_password": "hackpassword"}

    response = client.patch(
        f"/auth/utilisateurs/{test_admin.id}/password", json=payload, headers=headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_password_rotation_invalidates_old_login(
    client: TestClient, test_user: Utilisateur
):
    """Vérifie que l'ancien mot de passe est révoqué immédiatement."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    client.patch(
        f"/auth/utilisateurs/{test_user.id}/password",
        json={"current_password": "password123", "new_password": "NewPassword123!"},
        headers=headers,
    )

    response = client.post(
        "/auth/token", data={"username": test_user.username, "password": "password123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- TESTS DE SÉCURITÉ ET MIDDLEWARE ---


def test_active_status_middleware_enforcement(
    client: TestClient, test_user: Utilisateur, session: Session
):
    """Vérifie que le middleware bloque un utilisateur désactivé même avec un token valide."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    test_user.actif = False
    session.add(test_user)
    session.commit()

    response = client.get("/auth/users/me", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_route_access(
    client: TestClient, test_admin: Utilisateur, test_user: Utilisateur
):
    """Vérifie les accès RBAC sur les routes protégées."""
    admin_token, _ = create_access_token(data={"sub": test_admin.username})
    response = client.get(
        "/auth/admin-only", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == status.HTTP_200_OK

    user_token, _ = create_access_token(data={"sub": test_user.username})
    response = client.get(
        "/auth/admin-only", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_jwt_payload_contains_context(client: TestClient, test_admin: Utilisateur):
    """Audit du contenu (claims) du JWT."""
    response = client.post(
        "/auth/token", data={"username": test_admin.username, "password": "adminpass"}
    )
    token = response.json()["access_token"]
    payload = jwt.decode(token, stng.JWT_SECRET_KEY, algorithms=[stng.JWT_ALGORITHM])

    assert payload["sub"] == test_admin.username
    assert "context" in payload
    assert any(ctx["role"] == RoleName.ADMIN for ctx in payload["context"])
