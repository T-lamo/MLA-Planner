"""Tests pour GET /profiles/ministere/{ministere_id} et sécurisation campus."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from core.auth.security import create_access_token, get_password_hash
from models import AffectationRole, Membre, Role, Utilisateur
from models.schema_db_model import (
    MembreCampusLink,
    MembreMinistereLink,
)

# pylint: disable=redefined-outer-name


# ------------------------------------------------------------------ #
#  FIXTURES
# ------------------------------------------------------------------ #


@pytest.fixture
def membre_in_ministere(session: Session, seed_data: dict) -> Membre:
    """Membre rattaché au campus et au ministère de seed_data."""
    membre = session.exec(
        select(Membre).where(Membre.email == "membre.ministere@test.com")
    ).first()
    if not membre:
        membre = Membre(
            nom="Dupont",
            prenom="Marie",
            email="membre.ministere@test.com",
            campus_principal_id=seed_data["campus_id"],
        )
        session.add(membre)
        session.flush()
        session.add(
            MembreCampusLink(membre_id=membre.id, campus_id=seed_data["campus_id"])
        )
        session.add(
            MembreMinistereLink(membre_id=membre.id, ministere_id=seed_data["min_id"])
        )
        session.flush()
        session.refresh(membre)
    return membre


@pytest.fixture
def user_with_membre_read(
    session: Session, seed_data: dict, membre_in_ministere: Membre
) -> Utilisateur:
    """Utilisateur lié à un membre appartenant au ministère de seed_data."""
    role = session.exec(select(Role).where(Role.libelle == "MEMBRE_MLA")).first()
    if not role:
        role = Role(libelle="MEMBRE_MLA")
        session.add(role)
        session.flush()

    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "user_membre_read")
    ).first()
    if not user:
        user = Utilisateur(
            username="user_membre_read",
            password=get_password_hash("pass123"),
            actif=True,
            membre_id=membre_in_ministere.id,
        )
        session.add(user)
        session.flush()
        session.add(AffectationRole(utilisateur_id=user.id, role_id=role.id))
        session.flush()
        session.refresh(user)
    return user


@pytest.fixture
def membre_read_headers(user_with_membre_read: Utilisateur) -> dict:
    """Token pour un utilisateur lié à membre_in_ministere."""
    token, _ = create_access_token(data={"sub": user_with_membre_read.username})
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ #
#  GET /profiles/campus/{campus_id}/ — sécurisation
# ------------------------------------------------------------------ #


def test_campus_profiles_requires_auth(client: TestClient, seed_data: dict):
    cid = seed_data["campus_id"]
    resp = client.get(f"/profiles/campus/{cid}/")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_campus_profiles_ok_superadmin(
    client: TestClient,
    superadmin_headers: dict,
    seed_data: dict,
):
    cid = seed_data["campus_id"]
    resp = client.get(f"/profiles/campus/{cid}/", headers=superadmin_headers)
    assert resp.status_code == status.HTTP_200_OK
    assert "data" in resp.json()


# ------------------------------------------------------------------ #
#  GET /profiles/ministere/{ministere_id}
# ------------------------------------------------------------------ #


def test_ministere_profiles_requires_auth(client: TestClient, seed_data: dict):
    mid = seed_data["min_id"]
    resp = client.get(f"/profiles/ministere/{mid}")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_ministere_profiles_superadmin_bypass(
    client: TestClient,
    superadmin_headers: dict,
    seed_data: dict,
    membre_in_ministere: Membre,
):
    mid = seed_data["min_id"]
    cid = seed_data["campus_id"]
    resp = client.get(
        f"/profiles/ministere/{mid}",
        params={"campus_id": cid},
        headers=superadmin_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert isinstance(data, list)
    ids = [p["id"] for p in data]
    assert membre_in_ministere.id in ids


def test_ministere_profiles_plain_user_forbidden(
    client: TestClient,
    seed_data: dict,
    session: Session,
):
    """Un utilisateur sans aucune capability (plain user) est rejeté 403."""
    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "active_user")
    ).first()
    if not user:
        pytest.skip("Fixture active_user manquante")

    token, _ = create_access_token(data={"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    mid = seed_data["min_id"]
    resp = client.get(f"/profiles/ministere/{mid}", headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
