from uuid import uuid4

import pytest
from sqlmodel import Session

from models import Campus, Membre, Ministere, OrganisationICC, Pays, Pole


# pylint: disable=redefined-outer-name
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
    """Fixture pour créer un ministère lié à un campus via relation N:N."""
    ministere = Ministere(
        nom=f"Ministere {uuid4()}",
        date_creation="2024-01-01",
        actif=True,
    )
    # Relation Many-to-Many
    ministere.campuses = [test_campus]

    session.add(ministere)
    session.flush()
    session.refresh(ministere)
    return ministere


@pytest.fixture
def test_min(session: Session, test_campus: Campus) -> Ministere:
    """Version courte pour les tests de ministère."""
    minis = Ministere(
        nom=f"Ministere Initial {uuid4()}",
        date_creation="2024-01-01",
    )
    minis.campuses = [test_campus]
    session.add(minis)
    session.flush()
    session.refresh(minis)
    return minis


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
    """Fixture pour créer un membre valide avec sa relation Many-to-Many."""
    membre = Membre(
        nom="Soro",
        prenom="Jean",
        email=f"jean.{uuid4()}@test.com",
        actif=True,
        # campus_id supprimé ici
    )
    # On ajoute le campus à la collection N:N
    membre.campuses = [test_campus]

    session.add(membre)
    session.flush()
    session.refresh(membre)
    return membre
