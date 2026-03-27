from datetime import date, timedelta

import casbin  # type: ignore[import-untyped]
import pytest
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session

from core.auth import casbin_enforcer as _casbin_mod
from core.auth.auth_dependencies import (
    CasbinGuard,
    ScopedRoleChecker,
    _affectation_valide,
    get_active_campus,
)
from core.auth.security import create_access_token
from core.exceptions.app_exception import AppException
from core.settings import settings as stng
from mla_enum import RoleName
from models import Utilisateur

# pylint: disable=redefined-outer-name, unused-argument, too-many-arguments
# pylint: disable=too-many-positional-arguments

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
    client: TestClient,
    test_user,
    inactive_user,
    username,
    password,
    expected_status,
):
    """Teste les différents scénarios de login."""
    # Les données de formulaire (OAuth2PasswordRequestForm) sont envoyées en form-data,
    # donc pas besoin de jsonable_encoder ici, les chaînes suffisent.
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
        expires_delta=timedelta(minutes=-1),
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

    # Correction : str(test_user.id) pour l'URL
    response = client.patch(
        f"/auth/utilisateurs/{str(test_user.id)}/password",
        json=jsonable_encoder(payload),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_change_password_invalid_length(client: TestClient, test_user: Utilisateur):
    """Vérifie les contraintes Pydantic (min_length=6)."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"current_password": "password123", "new_password": "123"}
    response = client.patch(
        f"/auth/utilisateurs/{str(test_user.id)}/password",
        json=jsonable_encoder(payload),
        headers=headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_change_password_forbidden_for_other_user(
    client: TestClient, test_user: Utilisateur, test_admin: Utilisateur
):
    """Un utilisateur non-admin ne peut pas changer le mot de passe d'un tiers."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"current_password": "adminpass", "new_password": "hackpassword"}

    # Tentative de changement sur le compte admin
    response = client.patch(
        f"/auth/utilisateurs/{str(test_admin.id)}/password",
        json=jsonable_encoder(payload),
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_password_rotation_invalidates_old_login(
    client: TestClient, test_user: Utilisateur
):
    """Vérifie que l'ancien mot de passe est révoqué immédiatement."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    client.patch(
        f"/auth/utilisateurs/{str(test_user.id)}/password",
        json=jsonable_encoder(
            {"current_password": "password123", "new_password": "NewPassword123!"}
        ),
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
    """Vérifie que le middleware bloque un utilisateur désactivé."""
    token, _ = create_access_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    test_user.actif = False
    session.add(test_user)
    session.flush()

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
    # Conversion de l'énumération en string pour la comparaison si nécessaire
    assert any(
        ctx["role"] == RoleName.ADMIN.value or ctx["role"] == RoleName.ADMIN
        for ctx in payload["context"]
    )


def test_logout_and_token_invalidation(client: TestClient, test_user: Utilisateur):
    # 1. Login
    login_res = client.post(
        "/auth/token", data={"username": "active_user", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Vérifier
    me_res = client.get("/auth/users/me", headers=headers)
    assert me_res.status_code == 200

    # 3. Logout
    logout_res = client.post("/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # 4. Invalidation
    revoked_res = client.get("/auth/users/me", headers=headers)
    assert revoked_res.status_code == 401
    assert revoked_res.json()["detail"] == "Cette session a été fermée (déconnexion)"


# --- TESTS UNITAIRES : _affectation_valide ---


class _Aff:
    """Stub minimal pour tester _affectation_valide sans SQLModel."""

    def __init__(
        self,
        active: bool = True,
        date_debut: date | None = None,
        date_fin: date | None = None,
    ) -> None:
        self.active = active
        self.dateDebut = date_debut  # pylint: disable=invalid-name
        self.dateFin = date_fin  # pylint: disable=invalid-name


def test_affectation_valide_inactive() -> None:
    assert _affectation_valide(_Aff(active=False)) is False


def test_affectation_valide_date_fin_passee() -> None:
    hier = date.today() - timedelta(days=1)
    assert _affectation_valide(_Aff(date_fin=hier)) is False


def test_affectation_valide_date_debut_future() -> None:
    demain = date.today() + timedelta(days=1)
    assert _affectation_valide(_Aff(date_debut=demain)) is False


def test_affectation_valide_sans_dates() -> None:
    assert _affectation_valide(_Aff()) is True


def test_affectation_valide_dans_fenetre() -> None:
    hier = date.today() - timedelta(days=1)
    demain = date.today() + timedelta(days=1)
    assert _affectation_valide(_Aff(date_debut=hier, date_fin=demain)) is True


# --- TESTS UNITAIRES : ScopedRoleChecker ---


class _FakeRequest:
    """Stub minimal remplaçant fastapi.Request pour les tests unitaires."""

    def __init__(
        self,
        path_params: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.headers = headers or {}


class _FakeRole:
    def __init__(self, libelle: str) -> None:
        self.libelle = libelle


class _FakeContexte:
    def __init__(self, ministere_id: str) -> None:
        self.ministere_id = ministere_id


class _FakeAff:
    """Stub AffectationRole avec contextes optionnels."""

    def __init__(
        self,
        libelle: str,
        contextes: list | None = None,
        active: bool = True,
        date_debut: date | None = None,
        date_fin: date | None = None,
    ) -> None:
        self.role = _FakeRole(libelle)
        self.contextes = contextes or []
        self.active = active
        self.dateDebut = date_debut  # pylint: disable=invalid-name
        self.dateFin = date_fin  # pylint: disable=invalid-name


class _FakeUser:
    def __init__(self, affectations: list) -> None:
        self.affectations = affectations
        self.id: str = ""
        self.membre_id: str | None = None
        self.membre: object = None


def test_scoped_checker_global_role_no_contexte() -> None:
    """Affectation sans contexte → rôle global, accès accordé."""
    checker = ScopedRoleChecker(["RESPONSABLE_MLA"])
    user = _FakeUser([_FakeAff(RoleName.RESPONSABLE_MLA)])
    req = _FakeRequest(path_params={"ministere_id": "min-abc"})
    result = checker(req, user)  # type: ignore[arg-type]
    assert "RESPONSABLE_MLA" in result


def test_scoped_checker_contexte_match() -> None:
    """Contexte présent, ministere_id correspond → accès accordé."""
    checker = ScopedRoleChecker(["RESPONSABLE_MLA"])
    ctx = _FakeContexte("min-louange")
    user = _FakeUser([_FakeAff(RoleName.RESPONSABLE_MLA, contextes=[ctx])])
    req = _FakeRequest(path_params={"ministere_id": "min-louange"})
    result = checker(req, user)  # type: ignore[arg-type]
    assert "RESPONSABLE_MLA" in result


def test_scoped_checker_contexte_mismatch() -> None:
    """Contexte présent, ministere_id différent → 403."""
    checker = ScopedRoleChecker(["RESPONSABLE_MLA"])
    ctx = _FakeContexte("min-louange")
    user = _FakeUser([_FakeAff(RoleName.RESPONSABLE_MLA, contextes=[ctx])])
    req = _FakeRequest(path_params={"ministere_id": "min-technique"})
    with pytest.raises(HTTPException) as exc:
        checker(req, user)  # type: ignore[arg-type]
    assert exc.value.status_code == 403


def test_scoped_checker_super_admin_bypass() -> None:
    """Super Admin bypass total : contexte restreint ignoré."""
    checker = ScopedRoleChecker(["RESPONSABLE_MLA"])
    ctx = _FakeContexte("min-louange")
    user = _FakeUser([_FakeAff(RoleName.SUPER_ADMIN, contextes=[ctx])])
    req = _FakeRequest(path_params={"ministere_id": "min-technique"})
    result = checker(req, user)  # type: ignore[arg-type]
    assert result == ["SUPER_ADMIN"]


def test_scoped_checker_no_ministere_id_in_request() -> None:
    """Sans ministere_id dans la requête, le check de scope est ignoré (graceful)."""
    checker = ScopedRoleChecker(["RESPONSABLE_MLA"])
    ctx = _FakeContexte("min-louange")
    user = _FakeUser([_FakeAff(RoleName.RESPONSABLE_MLA, contextes=[ctx])])
    req = _FakeRequest()
    result = checker(req, user)  # type: ignore[arg-type]
    assert "RESPONSABLE_MLA" in result


# --- TESTS UNITAIRES/INTÉGRATION : get_active_campus ---


def test_get_active_campus_from_header(
    session: Session, test_campus, test_membre, test_user
):
    """Header X-Campus-Id présent + membre lié → retourne campus_id."""
    test_user.membre_id = test_membre.id
    session.add(test_user)
    session.flush()

    req = _FakeRequest(headers={"X-Campus-Id": test_campus.id})
    campus_id = get_active_campus(
        req, db=session, user=test_user  # type: ignore[arg-type]
    )
    assert campus_id == test_campus.id


def test_get_active_campus_from_principal(
    session: Session, test_campus, test_membre, test_user
):
    """Pas de header, campus_principal_id défini + membre lié → retourne campus_id."""
    test_membre.campus_principal_id = test_campus.id
    test_user.membre_id = test_membre.id
    test_user.membre = test_membre
    session.add(test_membre)
    session.add(test_user)
    session.flush()

    req = _FakeRequest()
    campus_id = get_active_campus(
        req, db=session, user=test_user  # type: ignore[arg-type]
    )
    assert campus_id == test_campus.id


def test_get_active_campus_no_campus_raises_400() -> None:
    """Ni header ni campus_principal_id → AppException AUTH_007 (400)."""
    user = _FakeUser([])
    user.membre_id = None
    user.membre = None
    req = _FakeRequest()
    with pytest.raises(AppException) as exc:
        get_active_campus(req, db=None, user=user)  # type: ignore[arg-type]
    assert exc.value.http_status == 400


def test_get_active_campus_unlinked_member_raises_403(
    session: Session, test_campus, test_membre, test_user
):
    """Campus fourni mais membre non lié → AppException AUTH_008 (403)."""
    other_campus_id = "campus-not-linked"
    test_user.membre_id = test_membre.id
    session.add(test_user)
    session.flush()

    req = _FakeRequest(headers={"X-Campus-Id": other_campus_id})
    with pytest.raises(AppException) as exc:
        get_active_campus(req, db=session, user=test_user)  # type: ignore[arg-type]
    assert exc.value.http_status == 403


def test_get_active_campus_super_admin_bypass() -> None:
    """Super Admin avec campus non lié → bypass, retourne campus_id."""
    user = _FakeUser([_FakeAff(RoleName.SUPER_ADMIN)])
    user.membre_id = None
    user.membre = None
    req = _FakeRequest(headers={"X-Campus-Id": "campus-xyz"})
    campus_id = get_active_campus(req, db=None, user=user)  # type: ignore[arg-type]
    assert campus_id == "campus-xyz"


# --- TESTS UNITAIRES : CasbinGuard ---


def _make_test_enforcer() -> casbin.Enforcer:
    """Enforcer Casbin en mémoire (pas de DB) pour les tests unitaires."""
    enf = casbin.Enforcer(_casbin_mod.CONF_PATH)
    enf.add_policy(RoleName.ADMIN.name, "*", "chants", "write")
    enf.add_policy(RoleName.MEMBRE_MLA.name, "*", "chants", "read")
    enf.add_grouping_policy("user-admin", RoleName.ADMIN.name, "*")
    enf.add_grouping_policy("user-membre", RoleName.MEMBRE_MLA.name, "*")
    return enf


def test_casbin_guard_allows_matching_policy(monkeypatch) -> None:  # type: ignore
    """Policy correspondante → accès accordé, user.id retourné."""
    monkeypatch.setattr(_casbin_mod, "get_enforcer", _make_test_enforcer)
    user = _FakeUser([])
    user.id = "user-admin"
    guard = CasbinGuard("chants", "write")
    result = guard(_FakeRequest(), user)  # type: ignore[arg-type]
    assert "user-admin" in result


def test_casbin_guard_denies_missing_policy(monkeypatch) -> None:  # type: ignore
    """Policy absente pour la ressource/action → 403."""
    monkeypatch.setattr(_casbin_mod, "get_enforcer", _make_test_enforcer)
    user = _FakeUser([])
    user.id = "user-membre"
    guard = CasbinGuard("chants", "write")
    with pytest.raises(HTTPException) as exc:
        guard(_FakeRequest(), user)  # type: ignore[arg-type]
    assert exc.value.status_code == 403


def test_casbin_guard_fallback_when_enforcer_none(monkeypatch) -> None:  # type: ignore
    """Enforcer non initialisé → délègue au RoleChecker (fallback_roles)."""
    monkeypatch.setattr(_casbin_mod, "get_enforcer", lambda: None)
    user = _FakeUser([_FakeAff(RoleName.ADMIN)])
    guard = CasbinGuard("chants", "write", fallback_roles=["ADMIN"])
    result = guard(_FakeRequest(), user)  # type: ignore[arg-type]
    assert "ADMIN" in result


def test_casbin_guard_super_admin_bypass(monkeypatch) -> None:  # type: ignore
    """Super Admin bypass Casbin même sans policy explicite."""
    monkeypatch.setattr(_casbin_mod, "get_enforcer", _make_test_enforcer)
    user = _FakeUser([_FakeAff(RoleName.SUPER_ADMIN)])
    user.id = "super-admin"
    guard = CasbinGuard("chants", "write")
    result = guard(_FakeRequest(), user)  # type: ignore[arg-type]
    assert result == [RoleName.SUPER_ADMIN.name]
