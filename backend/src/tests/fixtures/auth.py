import pytest
from sqlmodel import Session, select

from core.auth.security import create_access_token, get_password_hash
from mla_enum import RoleName
from models import AffectationRole, Role, Utilisateur


# pylint: disable=redefined-outer-name
@pytest.fixture
def test_user(session: Session) -> Utilisateur:
    """Crée un utilisateur standard actif (Get or Create)."""
    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "active_user")
    ).first()
    if not user:
        user = Utilisateur(
            username="active_user",
            password=get_password_hash("password123"),
            actif=True,
            email="active@test.com",
        )
        session.add(user)
        session.flush()
        session.refresh(user)
    return user


@pytest.fixture
def test_admin(session: Session) -> Utilisateur:
    """Crée un administrateur avec son rôle (Get or Create)."""
    # 1. Gestion du rôle
    admin_role = session.exec(
        select(Role).where(Role.libelle == RoleName.ADMIN)
    ).first()
    if not admin_role:
        admin_role = Role(libelle=RoleName.ADMIN)
        session.add(admin_role)
        session.flush()

    # 2. Gestion de l'utilisateur
    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "admin_user")
    ).first()
    if not user:
        user = Utilisateur(
            username="admin_user",
            password=get_password_hash("adminpass"),
            actif=True,
            email="admin@test.com",
        )
        session.add(user)
        session.flush()

        aff = AffectationRole(utilisateur_id=user.id, role_id=admin_role.id)
        session.add(aff)

    session.flush()
    session.refresh(user)
    return user


@pytest.fixture
def inactive_user(session: Session) -> Utilisateur:
    """Crée un utilisateur désactivé (Get or Create)."""
    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "banned_user")
    ).first()
    if not user:
        user = Utilisateur(
            username="banned_user",
            password=get_password_hash("password123"),
            actif=False,
            email="banned@test.com",
        )
        session.add(user)
        session.flush()
        session.refresh(user)
    return user


@pytest.fixture
def admin_headers(test_admin):
    # Remplace par ta vraie fonction de création de token
    token, _ = create_access_token(data={"sub": test_admin.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(test_user):
    token, _ = create_access_token(
        data={
            "sub": test_user.username,
            "user_id": str(test_user.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}
