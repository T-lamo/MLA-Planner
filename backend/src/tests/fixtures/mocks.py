from unittest.mock import MagicMock

import pytest

# Importations des modèles et services (ajuste selon ta structure)
from models import Membre
from services.membre_service import MembreService
from sqlalchemy.orm import Session


# pylint: disable=redefined-outer-name
@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def membre_service(mock_db):
    return MembreService(mock_db)


@pytest.fixture
def mock_membre():
    m = MagicMock(spec=Membre)
    m.id = "user-1"
    m.campus_id = "campus-1"
    return m
