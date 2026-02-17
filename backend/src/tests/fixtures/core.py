import os

import pytest
from conf.db.database import Database
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session, SQLModel

# On récupère l'engine configuré par notre factory (Postgres en local ou CI)
engine = Database.get_engine()

# --- PROTECTION CRITIQUE ---
engine = Database.get_engine()
db_url = str(engine.url)


@pytest.fixture(scope="session", autouse=True)
def force_test_db():
    """Vérifie qu'on n'écrase pas la base de prod ou de dev par erreur."""
    if "test" not in db_url.lower() and os.getenv("ENV") != "testing":
        pytest.exit(
            f"\n❌ ERREUR DE SÉCURITÉ : Les tests pointent sur"
            f"une base non-test : {db_url}\n"
            "Action : Crée une DB dédiée (ex: mla_test_db) ou utilise "
            "DATABASE_URL en ligne de commande."
        )


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Initialise le schéma de base de données une seule fois pour toute la session.
    """
    # Création des tables sur le vrai Postgres
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    # Optionnel : on peut drop à la fin, mais en CI le
    # container est détruit de toute façon


@pytest.fixture(name="session")
def session_fixture():
    connection = engine.connect()
    # On commence une transaction externe
    transaction = connection.begin()

    # On crée la session liée à cette connexion
    # "join_transaction_mode='create_savepoint'" permet de gérer les commits internes
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()  # On annule tout à la fin pour garder la DB propre
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Injecte la session de test dans FastAPI via dependency_overrides.
    """

    def get_session_override():
        yield session

    app.dependency_overrides[Database.get_session] = get_session_override
    app.dependency_overrides[Database.get_db_for_route] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
