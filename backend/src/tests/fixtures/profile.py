from datetime import date
from uuid import uuid4

import pytest
from sqlmodel import Session

from models.schema_db_model import (
    Campus,
    Ministere,
    OrganisationICC,
    Pays,
    Pole,
)

# --- FIXTURE DE DONNÉES ---


@pytest.fixture
def seed_data(session: Session):
    """
    Crée la chaîne de dépendances complète pour éviter les IntegrityError.
    """
    # 1. Organisation (La racine)
    org = OrganisationICC(
        id=str(uuid4()),
        nom=f"Organisation_{uuid4().hex[:6]}",
        date_creation=date(2020, 1, 1),
    )
    session.add(org)
    session.flush()

    # 2. Pays (Lié à l'organisation)
    pays = Pays(id=str(uuid4()), nom="France", code="FR", organisation_id=org.id)
    session.add(pays)
    session.flush()

    # 3. Campus (Lié au pays)
    campus = Campus(
        id=str(uuid4()),
        nom="Campus Paris",
        ville="Paris",
        pays_id=pays.id,
        timezone="Europe/Paris",
    )
    session.add(campus)
    session.flush()

    # 4. Ministère (Lié au campus)
    ministere = Ministere(
        id=str(uuid4()),
        nom="Ministère Test",
        campus_id=campus.id,
        date_creation=date(2024, 1, 1),
        actif=True,
    )
    session.add(ministere)
    session.flush()

    # 5. Pôle (Lié au ministère)
    pole = Pole(
        id=str(uuid4()), nom="Pôle Test", ministere_id=ministere.id, active=True
    )
    session.add(pole)

    session.commit()

    return {
        "org_id": org.id,
        "pays_id": pays.id,
        "campus_id": campus.id,
        "min_id": ministere.id,
        "pole_id": pole.id,
    }
