from uuid import uuid4

from fastapi import status
from models import Membre, Utilisateur

# --- TESTS DE CRÉATION & VALIDATION ---


def test_create_membre_invalid_uuid_format(client, admin_headers):
    payload = {
        "nom": "Doe",
        "prenom": "John",
        "pole_id": "pas-un-uuid",  # Déclenche désormais 422 grâce au type UUID
    }
    response = client.post("/membres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_membre_404_on_non_existent_pole(client, admin_headers, test_campus):
    """Vérifie la 404 si l'UUID est valide mais n'existe pas en base."""
    payload = {
        "nom": "Test",
        "prenom": "User",
        "pole_id": str(uuid4()),  # UUID valide mais inconnu
        "campus_id": test_campus.id,
        "email": f"test{uuid4()}@icc.com",
    }
    response = client.post("/membres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Pôle" in response.json()["detail"]


# --- TESTS DE LIAISON UTILISATEUR (CAS CRITIQUES) ---


def test_link_membre_full_lifecycle(
    client, admin_headers, session, test_user, test_campus
):
    """Vérifie l'unicité stricte entre membre et utilisateur."""
    # FIX: Ajout de campus_id pour respecter la contrainte NOT NULL
    m1 = Membre(
        nom="Membre1",
        prenom="P1",
        email=f"m1{uuid4()}@test.com",
        campus_id=test_campus.id,
    )
    m2 = Membre(
        nom="Membre2",
        prenom="P2",
        email=f"m2{uuid4()}@test.com",
        campus_id=test_campus.id,
    )
    session.add_all([m1, m2])
    session.flush()

    # Création d'un second utilisateur
    user2 = Utilisateur(
        username=f"u{uuid4()}", email=f"e{uuid4()}@t.com", password="hash", actif=True
    )
    session.add(user2)
    session.flush()

    # ACTION 1 : Lier m1 à test_user -> SUCCESS
    url = f"/membres/utilisateurs/{test_user.id}/link-membre?membre_id={m1.id}"
    res = client.patch(url, headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    assert "password" not in res.json()  # Sécurité : pas de password dans le Read

    # ACTION 2 : Tenter de lier m1 à user2 -> FAIL (Le membre a déjà un utilisateur)
    res = client.patch(
        f"/membres/utilisateurs/{user2.id}/link-membre?membre_id={m1.id}",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "déjà lié à un compte" in res.json()["detail"]

    # ACTION 3 : Tenter de lier m2 à test_user ->
    #  FAIL (L'utilisateur est déjà lié à un membre)
    res = client.patch(
        f"/membres/utilisateurs/{test_user.id}/link-membre?membre_id={m2.id}",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "déjà lié à un membre" in res.json()["detail"]


# --- TESTS DE SUPPRESSION & CASCADE ---


def test_delete_member_sets_user_link_to_null(
    client, admin_headers, session, test_user, test_campus
):
    """Vérifie le SET NULL sur l'utilisateur lors de la suppression du membre."""
    # FIX: Ajout de campus_id
    m = Membre(
        nom="User",
        prenom="Linked",
        email=f"l{uuid4()}@test.com",
        campus_id=test_campus.id,
    )
    session.add(m)
    session.flush()

    test_user.membre_id = m.id
    session.add(test_user)
    session.flush()

    # Suppression du membre
    client.delete(f"/membres/{m.id}", headers=admin_headers)

    # L'utilisateur doit toujours exister mais membre_id doit être None
    session.refresh(test_user)
    assert test_user.membre_id is None
    assert test_user.username == "active_user"


# --- TESTS DE LECTURE & RÉPONSE ---


def test_get_membre_read_schema_security(client, test_user, session, test_campus):
    """Vérifie la sécurité du schéma de lecture."""
    # FIX: Ajout de campus_id
    m = Membre(
        nom="Secu",
        prenom="Test",
        email=f"s{uuid4()}@test.com",
        campus_id=test_campus.id,
    )
    session.add(m)
    session.flush()

    test_user.membre_id = m.id
    session.add(test_user)
    session.flush()

    response = client.get(f"/membres/{m.id}")
    data = response.json()

    assert "utilisateur" in data
    if data["utilisateur"]:
        assert "password" not in data["utilisateur"]
        assert "username" in data["utilisateur"]
