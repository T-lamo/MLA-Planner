# pylint: disable=redefined-outer-name, unused-argument
from uuid import uuid4

import pytest
from sqlmodel import select

from models import Chantre, Instrument, Membre, Musicien, MusicienInstrument

# --- FIXTURES SPÉCIFIQUES ---


@pytest.fixture
def instrument_piano(session):
    """Fixture pour un instrument référentiel."""
    inst = Instrument(code="PIANO", nom="Piano Acoustique")
    session.add(inst)
    session.commit()
    session.refresh(inst)
    return inst


@pytest.fixture
def instrument_basse(session):
    """Fixture pour un second instrument référentiel."""
    inst = Instrument(code="BASSE", nom="Guitare Basse")
    session.add(inst)
    session.commit()
    session.refresh(inst)
    return inst


@pytest.fixture
def musicien_chantre(session, test_campus):
    """Crée la chaîne complète : Membre -> Chantre."""
    membre = Membre(
        nom="Musicos",
        prenom="Solo",
        email=f"music-{uuid4()}@test.com",
        campus_id=test_campus.id,
    )
    session.add(membre)
    session.flush()

    chantre = Chantre(membre_id=membre.id, niveau="Avancé")
    session.add(chantre)
    session.commit()
    session.refresh(chantre)
    return chantre


@pytest.fixture
def musicien_existant(session, musicien_chantre, instrument_piano):
    """Crée un musicien déjà en base avec un instrument."""
    musicien = Musicien(chantre_id=musicien_chantre.id)
    session.add(musicien)
    session.flush()

    liaison = MusicienInstrument(
        musicien_id=musicien.id, instrument_id=instrument_piano.id, is_principal=True
    )
    session.add(liaison)
    session.commit()
    session.refresh(musicien)
    return musicien


# --- TESTS ---


def test_create_musicien_success(
    client, musicien_chantre, instrument_piano, admin_headers
):
    """Vérifie la création complète via API avec instruments."""
    payload = {
        "chantre_id": str(musicien_chantre.id),
        "instruments_in": [
            {"instrument_id": str(instrument_piano.id), "is_principal": True}
        ],
    }

    response = client.post("/musiciens/", json=payload, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["chantre_id"] == str(musicien_chantre.id)
    assert len(data["instruments_assoc"]) == 1
    assert data["instruments_assoc"][0]["instrument_id"] == str(instrument_piano.id)


def test_get_musicien_by_id_with_relations(client, musicien_existant, user_headers):
    """Vérifie que le Read charge bien les relations et la property calculée."""
    response = client.get(f"/musiciens/{musicien_existant.id}", headers=user_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(musicien_existant.id)
    # Vérification de la liste des associations
    assert len(data["instruments_assoc"]) > 0
    assert data["instruments_assoc"][0]["is_principal"] is True


def test_update_musicien_replace_instruments(
    client, session, musicien_existant, instrument_basse, admin_headers
):
    """Vérifie que le service remplace correctement les instruments."""
    payload = {
        "instruments_in": [
            {"instrument_id": str(instrument_basse.id), "is_principal": True}
        ]
    }

    response = client.patch(
        f"/musiciens/{musicien_existant.id}", json=payload, headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérification API : l'instrument est mis à jour
    assert data["instruments_assoc"][0]["instrument_id"] == str(instrument_basse.id)

    # Vérification DB : l'ancienne liaison a été supprimée
    session.expire_all()
    stmt = select(MusicienInstrument).where(
        MusicienInstrument.musicien_id == musicien_existant.id
    )
    links = session.exec(stmt).all()
    assert len(links) == 1
    assert links[0].instrument_id == instrument_basse.id


def test_update_musicien_partial_no_instruments(
    client, session, musicien_existant, admin_headers
):
    """Vérifie qu'un patch sans 'instruments_in' conserve les instruments actuels."""
    # On envoie un payload sans la clé instruments_in
    payload = {"chantre_id": str(musicien_existant.chantre_id)}

    response = client.patch(
        f"/musiciens/{musicien_existant.id}", json=payload, headers=admin_headers
    )

    assert response.status_code == 200
    # L'instrument initial doit toujours être présent
    assert len(response.json()["instruments_assoc"]) == 1


def test_list_musiciens_paginated(client, session, musicien_existant, user_headers):
    """Vérifie la pagination héritée du BaseService."""
    response = client.get("/musiciens/?limit=10&offset=0", headers=user_headers)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) >= 1


def test_soft_delete_musicien(client, session, musicien_existant, admin_headers):
    """Vérifie que le musicien est marqué comme
    supprimé sans être effacé physiquement."""
    response = client.delete(
        f"/musiciens/{musicien_existant.id}", headers=admin_headers
    )
    assert response.status_code == 204

    session.expire_all()
    # On récupère l'objet via SQL direct car le repo filtre les deleted_at is None
    stmt = select(Musicien).where(Musicien.id == musicien_existant.id)
    db_m = session.exec(stmt).first()

    assert db_m is not None
    assert db_m.deleted_at is not None


def test_create_musicien_integrity_error(client, admin_headers):
    """Vérifie la gestion d'erreur sur un chantre_id invalide."""
    payload = {"chantre_id": str(uuid4()), "instruments_in": []}
    response = client.post("/musiciens/", json=payload, headers=admin_headers)

    # Erreur de clé étrangère
    assert response.status_code in [400, 404]
