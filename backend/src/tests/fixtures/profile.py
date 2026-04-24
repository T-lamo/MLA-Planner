from datetime import date
from uuid import uuid4

import pytest
from sqlmodel import Session

from models.schema_db_model import (
    Campus,
    Ministere,
    Organisation,
    Pole,
)

# --- FIXTURE DE DONNÉES ---


@pytest.fixture
def seed_data(session: Session):
    """
    Crée la chaîne de dépendances complète pour éviter les IntegrityError.
    """
    # 1. Organisation (La racine)
    org = Organisation(
        id=str(uuid4()),
        nom=f"Organisation_{uuid4().hex[:6]}",
        date_creation=date(2020, 1, 1),
    )
    session.add(org)
    session.flush()

    # 2. Campus (Lié à l'organisation)
    campus = Campus(
        id=str(uuid4()),
        nom="Campus Paris",
        ville="Paris",
        pays="France",
        organisation_id=org.id,
        timezone="Europe/Paris",
    )
    session.add(campus)
    session.flush()

    # 2b. Second campus (pour les tests multi-campus)
    campus2 = Campus(
        id=str(uuid4()),
        nom="Campus Lyon",
        ville="Lyon",
        pays="France",
        organisation_id=org.id,
        timezone="Europe/Paris",
    )
    session.add(campus2)
    session.flush()

    # 3. Ministère (Lié au campus)
    ministere = Ministere(
        id=str(uuid4()),
        nom="Ministère Test",
        date_creation=date(2024, 1, 1),
        actif=True,
    )
    ministere.campuses = [campus]
    session.add(ministere)
    session.flush()

    # 4. Pôle (Lié au ministère)
    pole = Pole(
        id=str(uuid4()), nom="Pôle Test", ministere_id=ministere.id, active=True
    )
    session.add(pole)

    session.commit()

    return {
        "org_id": org.id,
        "campus_id": campus.id,
        "campus2_id": campus2.id,
        "min_id": ministere.id,
        "pole_id": pole.id,
    }
