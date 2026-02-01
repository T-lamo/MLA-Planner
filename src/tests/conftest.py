import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from conf.db.database import Database
from core.auth.security import get_password_hash
from main import app
from mla_enum import RoleName
from models import AffectationRole, Role, Utilisateur

# pylint: disable=redefined-outer-name

# On récupère l'engine configuré par notre factory (Postgres en local ou CI)
engine = Database.get_engine()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Initialise le schéma de base de données une seule fois pour toute la session.
    """
    # Création des tables sur le vrai Postgres
    SQLModel.metadata.create_all(engine)
    yield
    # Optionnel : on peut drop à la fin, mais en CI le container est détruit de toute façon
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture():
    """
    Fournit une session isolée. Chaque test s'exécute dans une transaction
    qui subit un rollback à la fin pour garantir l'isolation des données.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Injecte la session de test dans FastAPI via dependency_overrides.
    """

    def get_session_override():
        yield session

    app.dependency_overrides[Database.get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# --- FIXTURES DE DONNÉES (SECURISÉES POUR POSTGRES) ---


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
        session.commit()
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

    session.commit()
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
        session.commit()
        session.refresh(user)
    return user
