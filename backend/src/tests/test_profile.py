from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from models import (
    ProfilCreateFull,
    ProfilUpdateFull,
    UtilisateurCreate,
    UtilisateurUpdate,
)
from models.schema_db_model import (
    Campus,
    CategorieRole,
    Membre,
    MinistereRoleConfig,
    RoleCompetence,
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

        with pytest.raises(AppException) as exc:
            service.create(profil_in)
        # ProfileService.create() rewrappe toutes les exceptions en
        # CORE_ACTION_IMPOSSIBLE
        assert exc.value.code == "CORE_002"

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

        with pytest.raises(AppException) as exc:
            service.get_one(invalid_id)
        # _get_db_obj lève AppException(ErrorRegistry.PROFIL_NOT_FOUND) → code PROF_001
        assert exc.value.code == "PROF_001"

    def test_create_profil_with_valid_role_codes(
        self, session: Session, seed_data, test_role_comp
    ):
        """Vérifie que les rôles sont correctement associés à la création."""
        service = ProfileService(session)

        # Arrange
        profil_in = ProfilCreateFull(
            nom="ROLE",
            prenom="Test",
            email=f"role_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            role_codes=[test_role_comp.code],
            utilisateur=UtilisateurCreate(
                username=f"role_user_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"role_{uuid4().hex[:6]}@test.com",
            ),
        )

        # Act
        result = service.create(profil_in)

        # Assert
        assert result.id is not None
        assert len(result.roles_assoc) == 1
        assert result.roles_assoc[0].role_code == test_role_comp.code

    def test_create_profil_with_invalid_role_codes(self, session: Session, seed_data):
        """Vérifie que ROLE_NOT_FOUND est rewrappé en
        CORE_ACTION_IMPOSSIBLE à la création."""
        service = ProfileService(session)

        # Arrange
        profil_in = ProfilCreateFull(
            nom="INVALID",
            prenom="Role",
            email=f"invalid_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            role_codes=["CODE_QUI_NEXISTE_PAS"],
            utilisateur=UtilisateurCreate(
                username=f"invalid_u_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"invalid_{uuid4().hex[:6]}@test.com",
            ),
        )

        # Act & Assert : ProfileService.create() rewrappe en CORE_ACTION_IMPOSSIBLE
        with pytest.raises(AppException) as exc:
            service.create(profil_in)
        assert exc.value.code == "CORE_002"

    def test_sync_roles_differential(self, session: Session, seed_data, test_role_comp):
        """Vérifie l'ajout puis la suppression différentielle des rôles via update."""
        service = ProfileService(session)

        # Arrange : création sans rôle
        profil_in = ProfilCreateFull(
            nom="SYNC",
            prenom="Roles",
            email=f"sync_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username=f"sync_u_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"sync_{uuid4().hex[:6]}@test.com",
            ),
        )
        created = service.create(profil_in)
        assert len(created.roles_assoc) == 0

        # Act : ajout d'un rôle
        updated = service.update(
            created.id, ProfilUpdateFull(role_codes=[test_role_comp.code])
        )
        assert len(updated.roles_assoc) == 1
        assert updated.roles_assoc[0].role_code == test_role_comp.code

        # Act : suppression du rôle
        cleared = service.update(created.id, ProfilUpdateFull(role_codes=[]))
        assert len(cleared.roles_assoc) == 0

    def test_list_paginated_with_campus_filter(self, session: Session, seed_data):
        """Vérifie que list_paginated filtre correctement par campus_id."""
        service = ProfileService(session)

        # Arrange : créer un profil dans le campus de seed_data
        profil_in = ProfilCreateFull(
            nom="PAGINATED",
            prenom="Filter",
            email=f"pag_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username=f"pag_u_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"pag_{uuid4().hex[:6]}@test.com",
            ),
        )
        service.create(profil_in)

        # Act
        result = service.list_paginated(
            limit=10, offset=0, campus_id=seed_data["campus_id"]
        )

        # Assert
        assert result.total >= 1
        assert all(
            any(c.id == seed_data["campus_id"] for c in p.campuses) for p in result.data
        )

    def test_list_all_with_and_without_campus_filter(self, session: Session, seed_data):
        """Vérifie list_all sans filtre et avec filtre campus_id."""
        service = ProfileService(session)

        # Arrange
        profil_in = ProfilCreateFull(
            nom="LISTALL",
            prenom="Test",
            email=f"la_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username=f"la_u_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"la_{uuid4().hex[:6]}@test.com",
            ),
        )
        service.create(profil_in)

        # Act : sans filtre
        all_profiles = service.list_all()
        assert len(all_profiles) >= 1

        # Act : avec filtre campus_id
        filtered = service.list_all(campus_id=seed_data["campus_id"])
        assert len(filtered) >= 1
        assert all(
            any(c.id == seed_data["campus_id"] for c in p.campuses) for p in filtered
        )

    # --- TESTS CAMPUS PRINCIPAL ---

    def test_create_profil_auto_assigns_single_campus_principal(
        self, session: Session, seed_data
    ):
        """Un seul campus fourni → campus_principal_id auto-assigné."""
        service = ProfileService(session)

        profil_in = ProfilCreateFull(
            nom="PRINCIPAL",
            prenom="Auto",
            email=f"p1_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            utilisateur=UtilisateurCreate(
                username=f"p1_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p1_{uuid4().hex[:6]}@test.com",
            ),
        )
        result = service.create(profil_in)

        assert result.campus_principal_id == seed_data["campus_id"]

    def test_create_profil_no_auto_assign_multiple_campuses(
        self, session: Session, seed_data
    ):
        """Plusieurs campus sans campus_principal_id explicite → None."""
        service = ProfileService(session)

        # Créer un second campus

        campus2 = Campus(
            id=str(uuid4()),
            nom="Campus Lyon",
            ville="Lyon",
            pays_id=seed_data["pays_id"],
            timezone="Europe/Paris",
        )
        session.add(campus2)
        session.flush()

        profil_in = ProfilCreateFull(
            nom="MULTI",
            prenom="Campus",
            email=f"p2_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"], campus2.id],
            utilisateur=UtilisateurCreate(
                username=f"p2_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p2_{uuid4().hex[:6]}@test.com",
            ),
        )
        result = service.create(profil_in)

        assert result.campus_principal_id is None

    def test_create_profil_explicit_campus_principal_valid(
        self, session: Session, seed_data
    ):
        """campus_principal_id explicite et dans campus_ids → stocké."""
        service = ProfileService(session)

        profil_in = ProfilCreateFull(
            nom="EXPLICIT",
            prenom="Principal",
            email=f"p3_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            campus_principal_id=seed_data["campus_id"],
            utilisateur=UtilisateurCreate(
                username=f"p3_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p3_{uuid4().hex[:6]}@test.com",
            ),
        )
        result = service.create(profil_in)

        assert result.campus_principal_id == seed_data["campus_id"]

    def test_create_profil_invalid_campus_principal_raises_error(
        self, session: Session, seed_data
    ):
        """campus_principal_id hors campus_ids →
        CORE_ACTION_IMPOSSIBLE (create rewrap)."""
        service = ProfileService(session)

        profil_in = ProfilCreateFull(
            nom="INVALID",
            prenom="Principal",
            email=f"p4_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"]],
            campus_principal_id=str(uuid4()),  # ID inexistant
            utilisateur=UtilisateurCreate(
                username=f"p4_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p4_{uuid4().hex[:6]}@test.com",
            ),
        )

        with pytest.raises(AppException) as exc:
            service.create(profil_in)
        assert exc.value.code == "CORE_002"

    def test_update_clears_principal_when_principal_campus_removed(
        self, session: Session, seed_data
    ):
        """Retirer le campus principal de campus_ids
        → campus_principal_id auto-effacé."""
        service = ProfileService(session)

        campus2 = Campus(
            id=str(uuid4()),
            nom="Campus Bordeaux",
            ville="Bordeaux",
            pays_id=seed_data["pays_id"],
            timezone="Europe/Paris",
        )
        session.add(campus2)
        session.flush()

        # Créer avec 2 campus, principal = campus_id
        profil_in = ProfilCreateFull(
            nom="CLEAR",
            prenom="Principal",
            email=f"p5_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"], campus2.id],
            campus_principal_id=seed_data["campus_id"],
            utilisateur=UtilisateurCreate(
                username=f"p5_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p5_{uuid4().hex[:6]}@test.com",
            ),
        )
        created = service.create(profil_in)
        assert created.campus_principal_id == seed_data["campus_id"]

        # Update : enlever le campus principal → auto-assign sur campus2 (seul restant)
        updated = service.update(
            created.id,
            ProfilUpdateFull(campus_ids=[campus2.id]),
        )
        assert updated.campus_principal_id == campus2.id

    def test_update_explicit_campus_principal_on_update(
        self, session: Session, seed_data
    ):
        """campus_principal_id explicite sur update → validé et stocké."""
        service = ProfileService(session)

        campus2 = Campus(
            id=str(uuid4()),
            nom="Campus Nantes",
            ville="Nantes",
            pays_id=seed_data["pays_id"],
            timezone="Europe/Paris",
        )
        session.add(campus2)
        session.flush()

        profil_in = ProfilCreateFull(
            nom="SWITCH",
            prenom="Principal",
            email=f"p6_{uuid4().hex[:6]}@test.com",
            campus_ids=[seed_data["campus_id"], campus2.id],
            campus_principal_id=seed_data["campus_id"],
            utilisateur=UtilisateurCreate(
                username=f"p6_{uuid4().hex[:6]}",
                password="Password123!",
                email=f"p6_{uuid4().hex[:6]}@test.com",
            ),
        )
        created = service.create(profil_in)
        assert created.campus_principal_id == seed_data["campus_id"]

        # Changer le campus principal vers campus2
        updated = service.update(
            created.id,
            ProfilUpdateFull(campus_principal_id=campus2.id),
        )
        assert updated.campus_principal_id == campus2.id


# ------------------------------------------------------------------ #
#  RC-162 — Assignation sécurisée des rôles
# ------------------------------------------------------------------ #


def _setup_ministere_role(session: Session, ministere_id: str) -> RoleCompetence:
    """Helper : crée catégorie + rôle + lien MinistereRoleConfig."""
    cat = CategorieRole(
        code=f"CAT_{uuid4().hex[:4].upper()}",
        libelle="Cat RC162",
    )
    session.add(cat)
    session.flush()

    role = RoleCompetence(
        code=f"RC162_{uuid4().hex[:4].upper()}",
        libelle="Rôle RC-162",
        categorie_code=cat.code,
    )
    session.add(role)
    session.flush()

    cfg = MinistereRoleConfig(
        ministere_id=ministere_id,
        role_code=role.code,
    )
    session.add(cfg)
    session.flush()
    session.refresh(role)
    return role


def _create_profil_with_ministere(session: Session, seed_data: dict) -> tuple:
    """Helper : crée un profil lié à seed_data['min_id']."""
    service = ProfileService(session)
    profil_in = ProfilCreateFull(
        nom="RC162",
        prenom="Test",
        email=f"rc162_{uuid4().hex[:6]}@test.com",
        campus_ids=[seed_data["campus_id"]],
        ministere_ids=[seed_data["min_id"]],
        utilisateur=UtilisateurCreate(
            username=f"rc162_{uuid4().hex[:6]}",
            password="Password123!",
            email=f"rc162_{uuid4().hex[:6]}@test.com",
        ),
    )
    profil = service.create(profil_in)
    return service, profil


def test_sync_roles_allows_configured_role(session: Session, seed_data: dict) -> None:
    """Un rôle configuré pour le ministère du membre est accepté."""
    role = _setup_ministere_role(session, seed_data["min_id"])
    service, profil = _create_profil_with_ministere(session, seed_data)

    updated = service.update(profil.id, ProfilUpdateFull(role_codes=[role.code]))
    codes = [r.role_code for r in updated.roles_assoc]
    assert role.code in codes


def test_sync_roles_rejects_unconfigured_role(
    session: Session, seed_data: dict
) -> None:
    """Un rôle non configuré pour aucun ministère du membre → ROLE_008."""
    cat = CategorieRole(
        code=f"NOCAT_{uuid4().hex[:4].upper()}", libelle="No Config Cat"
    )
    session.add(cat)
    session.flush()
    role_no_cfg = RoleCompetence(
        code=f"NOCFG_{uuid4().hex[:4].upper()}",
        libelle="Rôle sans config",
        categorie_code=cat.code,
    )
    session.add(role_no_cfg)
    session.flush()

    service, profil = _create_profil_with_ministere(session, seed_data)

    with pytest.raises(AppException) as exc_info:
        service.update(profil.id, ProfilUpdateFull(role_codes=[role_no_cfg.code]))
    assert exc_info.value.code == "ROLE_008"


def test_sync_roles_bypasses_validation_without_ministere(
    session: Session, seed_data: dict
) -> None:
    """Un membre sans ministère peut recevoir des rôles (bypass)."""
    cat = CategorieRole(code=f"BYCAT_{uuid4().hex[:4].upper()}", libelle="Bypass Cat")
    session.add(cat)
    session.flush()
    role = RoleCompetence(
        code=f"BYPASS_{uuid4().hex[:4].upper()}",
        libelle="Rôle Bypass",
        categorie_code=cat.code,
    )
    session.add(role)
    session.flush()

    service = ProfileService(session)
    profil_in = ProfilCreateFull(
        nom="BYPASS",
        prenom="NoMin",
        email=f"bypass_{uuid4().hex[:6]}@test.com",
        campus_ids=[seed_data["campus_id"]],
        role_codes=[role.code],
        utilisateur=UtilisateurCreate(
            username=f"bypass_{uuid4().hex[:6]}",
            password="Password123!",
            email=f"bypass_{uuid4().hex[:6]}@test.com",
        ),
    )
    result = service.create(profil_in)
    codes = [r.role_code for r in result.roles_assoc]
    assert role.code in codes
