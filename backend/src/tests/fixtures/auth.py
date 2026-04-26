import pytest
from sqlmodel import Session, select

from core.auth.security import create_access_token, get_password_hash
from mla_enum import RoleName  # noqa: F401 — conservé pour token tests
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
        select(Role).where(Role.libelle == RoleName.ADMIN.value)
    ).first()
    if not admin_role:
        admin_role = Role(libelle=RoleName.ADMIN.value)
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
def test_superadmin(session: Session) -> Utilisateur:
    """Crée un superadmin avec son rôle (Get or Create)."""
    super_role = session.exec(
        select(Role).where(Role.libelle == RoleName.SUPER_ADMIN.value)
    ).first()
    if not super_role:
        super_role = Role(libelle=RoleName.SUPER_ADMIN.value)
        session.add(super_role)
        session.flush()

    user = session.exec(
        select(Utilisateur).where(Utilisateur.username == "superadmin_user")
    ).first()
    if not user:
        user = Utilisateur(
            username="superadmin_user",
            password=get_password_hash("superadminpass"),
            actif=True,
        )
        session.add(user)
        session.flush()

        aff = AffectationRole(utilisateur_id=user.id, role_id=super_role.id)
        session.add(aff)

    session.flush()
    session.refresh(user)
    return user


@pytest.fixture
def admin_headers(test_admin):
    admin_caps = [
        "CAMPUS_ADMIN",
        "MEMBRE_READ",
        "MEMBRE_CREATE",
        "MEMBRE_UPDATE",
        "MEMBRE_DELETE",
        "CHANT_READ",
        "CHANT_WRITE",
        "PLANNING_READ",
        "PLANNING_WRITE",
        "TEMPLATE_READ",
        "TEMPLATE_WRITE",
        "ROLE_READ",
        "ROLE_WRITE",
        "MINISTERE_READ",
        "MINISTERE_WRITE",
        "POLE_READ",
        "POLE_WRITE",
        "ACTIVITE_READ",
        "ACTIVITE_WRITE",
    ]
    token, _ = create_access_token(
        data={"sub": test_admin.username, "capabilities": admin_caps}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def superadmin_headers(test_superadmin):
    token, _ = create_access_token(data={"sub": test_superadmin.username})
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
