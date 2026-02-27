from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from core.exceptions import BadRequestException, NotFoundException
from models import (
    ProfilCreateFull,
    ProfilUpdateFull,
    UtilisateurCreate,
    UtilisateurUpdate,
)
from models.schema_db_model import (
    Membre,
)
from services.profile_service import ProfileService

# --- TESTS TEST PROFILE SERVICE ---


class TestProfileService:

    def test_create_profil_full_success(self, session: Session, seed_data):
        """Test la création atomique Membre + Utilisateur + Relations N:N."""
        service = ProfileService(session)

        # Données valides pour passer les validateurs Pydantic
        user_in = UtilisateurCreate(
            username=f"user_{uuid4().hex[:6]}",
            password="SecurePassword123!",
            email="contact@test.com",
        )

        profil_in = ProfilCreateFull(
            nom="KABONGO",
            prenom="Jean",
            email="contact@test.com",
            campus_ids=[seed_data["campus_id"]],
            ministere_ids=[seed_data["min_id"]],
            pole_ids=[seed_data["pole_id"]],
            utilisateur=user_in,
        )

        # Action
        result = service.create(profil_in)

        # Assertions
        assert result.id is not None
        assert result.utilisateur is not None
        assert result.utilisateur.username.startswith("user_")
        assert len(result.campuses) == 1
        assert len(result.poles) == 1
        assert result.poles[0].id == seed_data["pole_id"]

    def test_update_profil_with_user_data(self, session: Session, seed_data):
        """Vérifie que la mise à jour modifie aussi l'utilisateur lié."""
        service = ProfileService(session)

        # 1. Setup initial
        p_in = ProfilCreateFull(
            nom="Initial",
            prenom="User",
            email="init@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username="old_nick", password="Password123!", email="init@test.com"
            ),
        )
        created = service.create(p_in)

        # 2. Update du nom de famille et du username
        update_dto = ProfilUpdateFull(
            nom="Updated", utilisateur=UtilisateurUpdate(username="new_nick")
        )

        updated = service.update(created.id, update_dto)

        # Assertions
        assert updated.nom == "Updated"
        assert updated.utilisateur is not None
        assert updated.utilisateur.username == "new_nick"

    def test_create_profil_validation_error_pydantic(self):
        """Vérifie que Pydantic bloque les données malformées avant le service."""
        with pytest.raises(ValidationError):
            # Email invalide et password trop court (si configuré ainsi)
            UtilisateurCreate(username="ui", password="1", email="pas-un-email")

    def test_create_membre_missing_campus_error(self, session: Session):
        """Vérifie la règle métier du MembreService (via ProfileService)."""
        service = ProfileService(session)

        user_in = UtilisateurCreate(
            username="fail_user", password="Password123!", email="fail@test.com"
        )

        profil_in = ProfilCreateFull(
            nom="Test",
            prenom="Fail",
            email="fail@test.com",
            campus_ids=[],  # INTERDIT
            utilisateur=user_in,
        )

        with pytest.raises(BadRequestException) as exc:
            service.create(profil_in)
        assert "au moins un campus" in str(exc.value)

    def test_delete_profil_soft_delete(self, session: Session, seed_data):
        """Vérifie le soft delete et la rupture du lien utilisateur."""
        service = ProfileService(session)

        # 1. Création
        p_in = ProfilCreateFull(
            nom="To",
            prenom="Delete",
            email="del@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username="del_me", password="Password123!", email="del@test.com"
            ),
        )
        created = service.create(p_in)
        membre_id = created.id

        # 2. Suppression
        service.delete(membre_id)

        # 4. Vérification DB : le membre doit avoir deleted_at
        db_membre = session.get(Membre, membre_id)
        assert db_membre is not None
        assert db_membre.deleted_at is not None

    def test_get_one_profil_success(self, session: Session, seed_data):
        """Vérifie la récupération d'un profil et le chargement de ses relations."""
        service = ProfileService(session)

        # 1. Création d'un profil complet pour le test
        user_in = UtilisateurCreate(
            username="reading_user", password="Password123!", email="read@test.com"
        )
        profil_in = ProfilCreateFull(
            nom="LECTURE",
            prenom="Test",
            email="read@test.com",
            campus_ids=[seed_data["campus_id"]],
            ministere_ids=[seed_data["min_id"]],
            pole_ids=[seed_data["pole_id"]],
            utilisateur=user_in,
        )
        created = service.create(profil_in)

        # 2. Action : Récupération via get_one
        result = service.get_one(created.id)

        # 3. Assertions sur le chargement Eager (selectinload)
        assert result.id == created.id
        assert result.nom == "Lecture"

        # Vérification de l'utilisateur (chargé via selectinload)
        assert result.utilisateur is not None
        assert result.utilisateur.username == "reading_user"

        # Vérification des relations Many-to-Many
        assert len(result.campuses) == 1
        assert result.campuses[0].nom == "Campus Paris"

        assert len(result.ministeres) == 1
        assert result.ministeres[0].nom == "Ministère Test"

        assert len(result.poles) == 1
        assert result.poles[0].nom == "Pôle Test"

    def test_get_one_profil_not_found(self, session: Session):
        """Vérifie qu'une exception est levée pour un ID inexistant."""
        service = ProfileService(session)
        invalid_id = str(uuid4())

        with pytest.raises(NotFoundException) as exc:
            service.get_one(invalid_id)

        assert f"Profil {invalid_id} introuvable" in str(exc.value)
