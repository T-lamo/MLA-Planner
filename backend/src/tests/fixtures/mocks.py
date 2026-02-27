from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

# Importations des modèles et services (ajuste selon ta structure)
from models import Membre
from services.membre_service import MembreService


# pylint: disable=redefined-outer-name
@pytest.fixture
def mock_db():
    mock = MagicMock(spec=Session)
    mock.exec.return_value = MagicMock()
    return mock


@pytest.fixture
def membre_service(mock_db):
    return MembreService(mock_db)


@pytest.fixture
def mock_membre():
    # 1. Création du mock avec la spécification du modèle Membre
    m = MagicMock(spec=Membre)

    # 2. Champs scalaires de base
    m.id = "user-1"
    m.nom = "Dorceus"
    m.prenom = "Amos"
    m.email = "amos.new@icc.com"
    m.telephone = "0123456789"
    m.actif = True
    m.date_inscription = datetime.now()  # Indispensable pour MembreRead

    # 3. Simulation de la relation N:N (Liste d'objets et non d'IDs)
    # Ton service fait : target_campus_id = membre.campuses[0].id
    mock_campus = MagicMock()
    mock_campus.id = "campus-1"
    mock_campus.nom = "Campus Lille"
    mock_campus.ville = "Lille"
    mock_campus.pays_id = "pays-uuid-1"  # Requis si CampusRead le demande

    # On initialise les listes de relations (N:N)
    m.campuses = [mock_campus]
    m.ministeres = []
    m.poles = []
    m.roles_assoc = []
    m.utilisateur = None  # Ou un MagicMock(spec=Utilisateur) si besoin

    return m
