import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from conf.db.database import Database
from core.auth.security import create_access_token, get_password_hash
from main import app
from mla_enum import AffectationStatusCode, RoleName
from models import (
    Activite,
    AffectationRole,
    Campus,
    CategorieRole,
    Membre,
    Ministere,
    OrganisationICC,
    Pays,
    PlanningService,
    Pole,
    Role,
    RoleCompetence,
    Slot,
    StatutPlanning,
    Utilisateur,
)
from models.schema_db_model import Affectation, MembreRole, StatutAffectation

# pylint: disable=redefined-outer-name

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


@pytest.fixture
def test_org(session: Session) -> OrganisationICC:
    """Fixture globale pour créer une organisation."""
    org = OrganisationICC(
        nom=f"Org Test {uuid4()}", code=str(uuid4())[:5], date_creation="2024-01-01"
    )
    session.add(org)
    session.flush()
    session.refresh(org)
    return org


@pytest.fixture
def test_pays(session: Session, test_org: OrganisationICC) -> Pays:
    """Fixture globale pour créer un pays."""
    pays = Pays(
        nom=f"Pays {uuid4()}",
        code=str(uuid4())[:2].upper(),
        organisation_id=test_org.id,
        date_creation="2024-01-01",
    )
    session.add(pays)
    session.flush()
    session.refresh(pays)
    return pays


@pytest.fixture
def test_campus(session: Session, test_pays: Pays) -> Campus:
    """Fixture globale pour créer un campus."""
    campus = Campus(
        nom=f"Campus Test {uuid4()}",
        ville="Test Ville",
        pays_id=test_pays.id,
        date_creation="2024-01-01",
        deleted_at=None,
    )
    session.add(campus)
    session.flush()
    session.refresh(campus)
    return campus


@pytest.fixture
def test_ministere(session: Session, test_campus: Campus) -> Ministere:
    """Fixture pour créer un ministère lié à un campus."""

    ministere = Ministere(
        nom=f"Ministere {uuid4()}",
        date_creation="2024-01-01",
        campus_id=test_campus.id,
        actif=True,
    )
    session.add(ministere)
    session.flush()
    session.refresh(ministere)
    return ministere


@pytest.fixture
def test_pole(session: Session, test_ministere: Ministere) -> Pole:
    """Fixture pour créer un pôle lié à un ministère."""

    pole = Pole(
        nom=f"Pole Test {uuid4()}",
        description="Description test",
        ministere_id=test_ministere.id,
        active=True,
    )
    session.add(pole)
    session.flush()
    session.refresh(pole)
    return pole


@pytest.fixture
def test_membre(session: Session, test_campus: Campus) -> Membre:
    """Fixture pour créer un membre valide."""
    membre = Membre(
        nom="Soro",
        prenom="Jean",
        email=f"jean.{uuid4()}@test.com",
        actif=True,
        campus_id=test_campus.id,
    )
    session.add(membre)
    session.flush()
    session.refresh(membre)
    return membre


@pytest.fixture
def test_cat(session):
    """Crée une catégorie de base pour les rôles."""
    cat = CategorieRole(code="TECH", libelle="Technique")
    session.add(cat)
    session.flush()
    return cat


@pytest.fixture
def test_role_comp(session: Session, test_cat: CategorieRole) -> RoleCompetence:
    """Fixture pour créer un rôle de compétence lié à la catégorie de test."""
    role = RoleCompetence(
        code="DEV_PYTHON", libelle="Développeur Python", categorie_code=test_cat.code
    )
    session.add(role)
    session.flush()
    session.refresh(role)
    return role


@pytest.fixture
def test_activite(session: Session, test_campus, test_ministere) -> Activite:
    """
    Fixture pour créer une activité valide.
    Répond aux contraintes du nouveau schéma (type, ministere_organisateur, dates).
    """
    activite = Activite(
        nom=f"Activite Test {uuid4().hex[:6]}",
        type="Réunion",  # Valeur requise par la contrainte NOT NULL
        campus_id=test_campus.id,
        ministere_organisateur_id=test_ministere.id,
        date_debut=datetime.now(),
        date_fin=datetime.now() + timedelta(hours=2),
    )

    session.add(activite)
    session.flush()
    session.refresh(activite)
    return activite


@pytest.fixture
def activite_data(test_campus, test_ministere):
    return {
        "type": "Culte",
        "date_debut": (datetime.now() + timedelta(days=1)).isoformat(),
        "date_fin": (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
        "lieu": "Auditorium Principal",
        "description": "Culte dominical",
        "campus_id": test_campus.id,
        "ministere_organisateur_id": test_ministere.id,
    }


@pytest.fixture(autouse=True)
def seed_planning_status(session: Session):
    """Populate the reference table for statuses before each test."""
    codes = ["BROUILLON", "PUBLIE", "ANNULE"]
    for code in codes:
        # We use merge to avoid conflicts if the status already exists
        session.merge(StatutPlanning(code=code, libelle=code.capitalize()))
    session.flush()


@pytest.fixture
def test_slot(session, test_planning):
    """Fixture pour créer un Slot (créneau) valide."""
    # On définit des dates cohérentes avec l'activité parente si possible
    maintenant = datetime.now()
    slot = Slot(
        id=str(uuid4()),
        planning_id=test_planning.id,
        nom_creneau="Session de Louange",
        date_debut=maintenant + timedelta(hours=1),
        date_fin=maintenant + timedelta(hours=2),
    )
    session.add(slot)
    session.flush()
    session.refresh(slot)
    return slot


@pytest.fixture
def test_statut_brouillon(session):
    """
    Assure que le statut BROUILLON existe dans la table de référence.
    C'est crucial car statut_code est une foreign_key.
    """

    statut = session.get(StatutPlanning, "BROUILLON")
    if not statut:
        statut = StatutPlanning(code="BROUILLON")  # libelle="Brouillon"
        session.add(statut)
        session.flush()
        session.refresh(statut)
    return statut


@pytest.fixture
def test_planning(session, test_activite, test_statut_brouillon):
    """Fixture pour créer un PlanningService lié à une Activité."""
    planning = PlanningService(
        id=str(uuid4()),
        activite_id=test_activite.id,
        statut_code=test_statut_brouillon.code,
    )
    session.add(planning)
    session.flush()
    session.refresh(planning)
    return planning


@pytest.fixture
def test_membre_role(session, test_membre, test_role_comp):
    """
    Crée le lien MembreRole (MembreRole).
    """
    membre_role = MembreRole(
        membre_id=test_membre.id,
        role_code=test_role_comp.code,
        niveau="INTERMEDIAIRE",
        is_principal=True,
    )
    session.add(membre_role)
    session.flush()
    session.refresh(membre_role)
    return membre_role


@pytest.fixture(autouse=True)
def seed_affectation_status(session: Session):
    """Popule la table de référence des statuts d'affectation."""

    for status in AffectationStatusCode:
        session.merge(
            StatutAffectation(code=status.value, libelle=status.value.capitalize())
        )
    session.flush()


@pytest.fixture
def test_affectation(session, test_slot, test_membre) -> Affectation:
    """Fixture pour créer une affectation valide liée à un slot et un membre."""

    # On s'assure que le statut existe (déjà fait par seed_affectation_status en autouse)

    affectation = Affectation(
        slot_id=test_slot.id,
        membre_id=test_membre.id,
        role_code="ROLE_TEST",
        # Par défaut dans le workflow, une affectation est PROPOSE
        statut_affectation_code=AffectationStatusCode.PROPOSE.value,
        presence_confirmee=False,
    )

    session.add(affectation)
    # Important : flush() au lieu de flush() pour ne pas fermer
    # la transaction de la session de test
    session.flush()
    session.refresh(affectation)
    return affectation
