from uuid import uuid4

from fastapi import status

from models import Chantre, Membre, Utilisateur

# --- TESTS DE CRÉATION & VALIDATION ---


def test_create_membre_invalid_uuid_format(client, admin_headers):
    payload = {
        "nom": "Doe",
        "prenom": "John",
        "pole_id": "pas-un-uuid",  # Déclenche désormais 422 grâce au type UUID
    }
    response = client.post("/membres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_membre_404_on_non_existent_pole(client, admin_headers):
    """Vérifie la 404 si l'UUID est valide mais n'existe pas en base."""
    payload = {
        "nom": "Test",
        "prenom": "User",
        "pole_id": str(uuid4()),  # UUID valide mais inconnu
        "email": f"test{uuid4()}@icc.com",
    }
    response = client.post("/membres/", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Pôle" in response.json()["detail"]


# --- TESTS DE LIAISON UTILISATEUR (CAS CRITIQUES) ---


def test_link_membre_full_lifecycle(client, admin_headers, session, test_user):
    """
    Vérifie l'unicité stricte :
    1. Un membre ne peut avoir qu'un utilisateur.
    2. Un utilisateur ne peut être lié qu'à un seul membre.
    """
    # Création des membres
    m1 = Membre(nom="Membre1", prenom="P1", email=f"m1{uuid4()}@test.com")
    m2 = Membre(nom="Membre2", prenom="P2", email=f"m2{uuid4()}@test.com")
    session.add_all([m1, m2])
    session.commit()

    # Création d'un second utilisateur
    user2 = Utilisateur(
        username=f"u{uuid4()}", email=f"e{uuid4()}@t.com", password="hash", actif=True
    )
    session.add(user2)
    session.commit()

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


def test_cascade_delete_member_removes_chantre(client, admin_headers, session):
    # Setup
    m = Membre(nom="Chantre", prenom="Test", email="c@test.com")
    session.add(m)
    session.commit()
    c = Chantre(membre_id=m.id, nom_de_scene="Star")
    session.add(c)
    session.commit()

    # Action
    response = client.delete(f"/membres/{m.id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Vérification
    session.expire_all()
    # Le membre existe encore en base (pour le Big Data)
    member_in_db = session.get(Membre, m.id)
    assert member_in_db.deleted_at is not None

    # Mais le chantre a été nettoyé (ou soft-deleté selon ton choix)
    assert session.get(Chantre, c.id) is None


def test_delete_member_sets_user_link_to_null(
    client, admin_headers, session, test_user
):
    """Vérifie que supprimer un membre ne supprime pas l'utilisateur
    mais casse le lien (SET NULL)."""
    m = Membre(nom="User", prenom="Linked", email=f"l{uuid4()}@test.com")
    session.add(m)
    session.commit()

    test_user.membre_id = m.id
    session.add(test_user)
    session.commit()

    # Suppression du membre
    client.delete(f"/membres/{m.id}", headers=admin_headers)

    # L'utilisateur doit toujours exister mais membre_id doit être None
    session.refresh(test_user)
    assert test_user.membre_id is None
    assert test_user.username == "active_user"


# --- TESTS DE LECTURE & RÉPONSE ---


def test_get_membre_read_schema_security(client, test_user, session):
    """Vérifie que le schéma MembreRead n'inclut jamais
    d'infos sensibles de l'utilisateur."""
    m = Membre(nom="Secu", prenom="Test", email=f"s{uuid4()}@test.com")
    session.add(m)
    session.commit()

    test_user.membre_id = m.id
    session.add(test_user)
    session.commit()

    response = client.get(f"/membres/{m.id}")
    data = response.json()

    assert "utilisateur" in data
    if data["utilisateur"]:
        assert "password" not in data["utilisateur"]
        assert "username" in data["utilisateur"]
