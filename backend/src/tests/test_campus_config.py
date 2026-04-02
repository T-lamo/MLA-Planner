"""
Tests du module Campus Configuration.

Prérequis : la fixture `session` est fournie par tests/fixtures/core.py.
Les fixtures `test_campus` et `test_ministere` viennent de
tests/fixtures/geo.py (chargées via conftest.py).
"""

from uuid import uuid4

import pytest
from sqlmodel import Session, select

from core.exceptions.app_exception import AppException
from models.schema_db_model import (
    Campus,
    CategorieRole,
    Membre,
    MembreRole,
    Ministere,
    MinistereRoleConfig,
)
from services.campus_config_service import CampusConfigService

# ------------------------------------------------------------------ #
#  Fixtures locales
# ------------------------------------------------------------------ #

# pylint: disable=redefined-outer-name


@pytest.fixture
def config_svc(session: Session) -> CampusConfigService:
    """Retourne une instance du service de configuration."""
    return CampusConfigService(session)


# ------------------------------------------------------------------ #
#  Statuts
# ------------------------------------------------------------------ #


def test_init_statuts_idempotent(
    config_svc: CampusConfigService,
) -> None:
    """init_statuts() appelé 2× ne crée pas de doublons."""
    plannings1, affectations1 = config_svc.init_statuts()
    plannings2, affectations2 = config_svc.init_statuts()

    codes1 = {sp.code for sp in plannings1}
    codes2 = {sp.code for sp in plannings2}
    assert codes1 == codes2

    aff_codes1 = {sa.code for sa in affectations1}
    aff_codes2 = {sa.code for sa in affectations2}
    assert aff_codes1 == aff_codes2

    assert "BROUILLON" in codes1
    assert "PUBLIE" in codes1
    assert "PROPOSE" in aff_codes1
    assert "CONFIRME" in aff_codes1


# ------------------------------------------------------------------ #
#  Ministères
# ------------------------------------------------------------------ #


def test_add_ministere_creates_new(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Un ministère inexistant est créé et lié au campus."""
    nom = f"NouveauMin-{uuid4()}"
    ministere, created, linked = config_svc.add_ministere_to_campus(
        str(test_campus.id), nom
    )
    assert created is True
    assert linked is True
    assert ministere.nom == nom


def test_add_ministere_reuses_existing(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Un ministère au même nom mais non lié → created=False, linked=True."""
    nom = f"MinistereExistant-{uuid4()}"
    # Créer le ministère sans le lier au campus
    existing = Ministere(nom=nom, date_creation="2024-01-01", actif=True)
    session.add(existing)
    session.flush()
    session.refresh(existing)

    ministere, created, linked = config_svc.add_ministere_to_campus(
        str(test_campus.id), nom
    )
    assert created is False
    assert linked is True
    assert ministere.id == existing.id


def test_add_ministere_already_linked(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Appel 2× avec même nom → 2ème : created=False, linked=False."""
    nom = f"MinDouble-{uuid4()}"
    _, created1, linked1 = config_svc.add_ministere_to_campus(str(test_campus.id), nom)
    _, created2, linked2 = config_svc.add_ministere_to_campus(str(test_campus.id), nom)
    assert created1 is True
    assert linked1 is True
    assert created2 is False
    assert linked2 is False


def test_remove_ministere_link_not_delete_entity(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Après remove_ministere_from_campus(), l'entité Ministere existe encore."""
    nom = f"MinRemove-{uuid4()}"
    ministere, _, _ = config_svc.add_ministere_to_campus(str(test_campus.id), nom)
    ministere_id = str(ministere.id)

    config_svc.remove_ministere_from_campus(str(test_campus.id), ministere_id)

    still_exists = session.get(Ministere, ministere_id)
    assert still_exists is not None


def test_remove_ministere_link_not_found_raises(
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Un ministere_id non lié lève CONF_MINISTERE_LINK_NOT_FOUND."""
    with pytest.raises(AppException) as exc_info:
        config_svc.remove_ministere_from_campus(str(test_campus.id), str(uuid4()))
    assert exc_info.value.code == "CONF_003"


# ------------------------------------------------------------------ #
#  Catégories
# ------------------------------------------------------------------ #


def _create_linked_ministere(
    session: Session,
    config_svc: CampusConfigService,
    campus: Campus,
) -> Ministere:
    """Helper : crée un ministère lié à un campus."""
    nom = f"MinCat-{uuid4()}"
    ministere, _, _ = config_svc.add_ministere_to_campus(str(campus.id), nom)
    return ministere


def test_add_categorie_creates_new(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Une catégorie inexistante est créée dans le ministère."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    nom = f"Chant-{uuid4()}"

    categorie, created = config_svc.add_categorie_to_ministere(str(ministere.id), nom)
    assert created is True
    assert categorie.libelle == nom


def test_add_categorie_reuses_existing(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Même nom + même ministere_id → created=False au 2ème appel."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    nom = f"CatDouble-{uuid4()}"

    _, created1 = config_svc.add_categorie_to_ministere(str(ministere.id), nom)
    _, created2 = config_svc.add_categorie_to_ministere(str(ministere.id), nom)
    assert created1 is True
    assert created2 is False


# ------------------------------------------------------------------ #
#  Rôles Compétence
# ------------------------------------------------------------------ #


def _setup_categorie(
    session: Session,
    config_svc: CampusConfigService,
    campus: Campus,
) -> CategorieRole:
    """Helper : crée ministère + catégorie pour les tests de rôle."""
    ministere = _create_linked_ministere(session, config_svc, campus)
    cat, _ = config_svc.add_categorie_to_ministere(str(ministere.id), f"Cat-{uuid4()}")
    return cat


def test_add_role_competence_creates_new(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Un rôle inexistant est créé dans la catégorie."""
    cat = _setup_categorie(session, config_svc, test_campus)
    code = f"VOX{uuid4().hex[:4].upper()}"

    role, created = config_svc.add_role_competence_to_categorie(
        cat.code, code, "Voix Test"
    )
    assert created is True
    assert role.code == code
    assert role.categorie_code == cat.code


def test_add_role_competence_idempotent(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Même code + même catégorie → created=False au 2ème appel."""
    cat = _setup_categorie(session, config_svc, test_campus)
    code = f"IDM{uuid4().hex[:4].upper()}"

    _, created1 = config_svc.add_role_competence_to_categorie(cat.code, code, "Libellé")
    _, created2 = config_svc.add_role_competence_to_categorie(cat.code, code, "Libellé")
    assert created1 is True
    assert created2 is False


def test_add_role_competence_code_conflict(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Même code dans une autre catégorie → AppException CONF_ROLE_CODE_CONFLICT."""
    cat1 = _setup_categorie(session, config_svc, test_campus)
    cat2 = _setup_categorie(session, config_svc, test_campus)
    code = f"CONF{uuid4().hex[:4].upper()}"

    config_svc.add_role_competence_to_categorie(cat1.code, code, "Rôle 1")

    with pytest.raises(AppException) as exc_info:
        config_svc.add_role_competence_to_categorie(cat2.code, code, "Rôle 2")
    assert exc_info.value.code == "CONF_004"


def test_delete_role_competence_in_use(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
    test_ministere: Ministere,
) -> None:
    """Un rôle utilisé par un membre lève CONF_ROLE_IN_USE."""

    cat = _setup_categorie(session, config_svc, test_campus)
    code = f"USE{uuid4().hex[:4].upper()}"
    role, _ = config_svc.add_role_competence_to_categorie(
        cat.code, code, "Rôle Utilisé"
    )

    # Créer un membre minimal
    membre = Membre(
        nom="Dupont",
        prenom="Test",
        email=f"test.{uuid4()}@example.com",
        actif=True,
    )
    session.add(membre)
    session.flush()
    session.refresh(membre)

    # Lier le membre au rôle
    membre_role = MembreRole(
        membre_id=str(membre.id),
        role_code=role.code,
    )
    session.add(membre_role)
    session.flush()

    with pytest.raises(AppException) as exc_info:
        config_svc.delete_role_competence(cat.code, code)
    assert exc_info.value.code == "CONF_005"


# ------------------------------------------------------------------ #
#  RBAC
# ------------------------------------------------------------------ #


def test_init_rbac_roles_idempotent(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """2ème appel → created_count=0."""
    nom = f"MinRbac-{uuid4()}"
    ministere, _, _ = config_svc.add_ministere_to_campus(str(test_campus.id), nom)

    roles1, count1 = config_svc.init_rbac_roles_for_ministere(
        str(test_campus.id), str(ministere.id)
    )
    _, count2 = config_svc.init_rbac_roles_for_ministere(
        str(test_campus.id), str(ministere.id)
    )

    assert len(roles1) == 4
    assert count1 >= 0
    assert count2 == 0


# ------------------------------------------------------------------ #
#  Résumé campus
# ------------------------------------------------------------------ #


def test_campus_config_summary_keys(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Le résumé contient les clés obligatoires."""
    config_svc.init_statuts()
    summary = config_svc.get_campus_summary(str(test_campus.id))

    assert "campus_id" in summary
    assert "campus_nom" in summary
    assert "ministeres" in summary
    assert "statuts_planning" in summary
    assert "statuts_affectation" in summary
    assert summary["campus_id"] == str(test_campus.id)
    assert isinstance(summary["ministeres"], list)
    assert isinstance(summary["statuts_planning"], list)
    assert isinstance(summary["statuts_affectation"], list)


# ------------------------------------------------------------------ #
#  Listing global ministères / catégories
# ------------------------------------------------------------------ #


def test_list_all_ministeres_returns_all(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """list_all_ministeres retourne tous les ministères actifs."""
    nom1 = f"MinA-{uuid4()}"
    nom2 = f"MinB-{uuid4()}"
    config_svc.add_ministere_to_campus(str(test_campus.id), nom1)
    config_svc.add_ministere_to_campus(str(test_campus.id), nom2)

    result = config_svc.list_all_ministeres()
    noms = [m.nom for m in result]
    assert nom1 in noms
    assert nom2 in noms


# ------------------------------------------------------------------ #
#  Même nom de catégorie dans deux ministères différents
# ------------------------------------------------------------------ #


def test_same_category_name_in_two_ministeres(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """
    Catalogue global RC-158 : même libellé → même catégorie réutilisée.
    Le 2ème appel retourne created=False (find-or-create sur libellé).
    """
    nom_commun = f"Chantres-{uuid4()}"
    min_a, _, _ = config_svc.add_ministere_to_campus(
        str(test_campus.id), f"MLA-{uuid4()}"
    )
    min_b, _, _ = config_svc.add_ministere_to_campus(
        str(test_campus.id), f"Jeunes-{uuid4()}"
    )

    cat_a, created_a = config_svc.add_categorie_to_ministere(str(min_a.id), nom_commun)
    cat_b, created_b = config_svc.add_categorie_to_ministere(str(min_b.id), nom_commun)

    assert created_a is True
    # Catalogue global : la catégorie existait déjà, même code retourné
    assert created_b is False
    assert cat_a.code == cat_b.code
    assert cat_a.libelle == cat_b.libelle == nom_commun


# ------------------------------------------------------------------ #
#  MinistereRoleConfig (RC-160)
# ------------------------------------------------------------------ #


def _setup_role(
    session: Session,
    config_svc: CampusConfigService,
    campus: Campus,
) -> tuple:
    """Helper : crée ministère + catégorie + rôle compétence."""
    cat = _setup_categorie(session, config_svc, campus)
    code = f"RL{uuid4().hex[:4].upper()}"
    role, _ = config_svc.add_role_competence_to_categorie(cat.code, code, "Rôle Test")
    return role, cat


def test_activate_role_creates_config(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """activate_role_for_ministere crée le lien et retourne created=True."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    role, _ = _setup_role(session, config_svc, test_campus)

    config, created = config_svc.activate_role_for_ministere(
        str(ministere.id), role.code
    )
    assert created is True
    assert config.ministere_id == str(ministere.id)
    assert config.role_code == role.code


def test_activate_role_idempotent(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """2ème activation du même rôle → created=False, pas d'exception."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    role, _ = _setup_role(session, config_svc, test_campus)

    _, created1 = config_svc.activate_role_for_ministere(str(ministere.id), role.code)
    _, created2 = config_svc.activate_role_for_ministere(str(ministere.id), role.code)
    assert created1 is True
    assert created2 is False


def test_deactivate_role_removes_config(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """deactivate_role_for_ministere supprime le lien sans supprimer le rôle."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    role, _ = _setup_role(session, config_svc, test_campus)

    config_svc.activate_role_for_ministere(str(ministere.id), role.code)
    config_svc.deactivate_role_for_ministere(str(ministere.id), role.code)

    roles = config_svc.list_roles_of_ministere(str(ministere.id))
    codes = [r.code for r in roles]
    assert role.code not in codes


def test_deactivate_role_not_found_raises(
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """Désactiver un rôle non activé lève MINST_ROLE_NOT_FOUND (ROLE_007)."""
    with pytest.raises(AppException) as exc_info:
        config_svc.deactivate_role_for_ministere(str(uuid4()), "INEXISTANT")
    assert exc_info.value.code == "ROLE_007"


def test_activate_category_batch(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """activate_category_for_ministere active tous les rôles de la catégorie."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    cat, _ = config_svc.add_categorie_to_ministere(
        str(ministere.id), f"CatBatch-{uuid4()}"
    )
    for i in range(3):
        code = f"BCH{uuid4().hex[:3].upper()}{i}"
        config_svc.add_role_competence_to_categorie(cat.code, code, f"Rôle {i}")

    count = config_svc.activate_category_for_ministere(str(ministere.id), cat.code)
    assert count == 3

    roles = config_svc.list_roles_of_ministere(str(ministere.id))
    assert len(roles) >= 3


def test_activate_category_idempotent(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """2ème activate_category_for_ministere → count=0."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    cat, _ = config_svc.add_categorie_to_ministere(
        str(ministere.id), f"CatIdem-{uuid4()}"
    )
    code = f"IDC{uuid4().hex[:4].upper()}"
    config_svc.add_role_competence_to_categorie(cat.code, code, "Rôle Idem")

    count1 = config_svc.activate_category_for_ministere(str(ministere.id), cat.code)
    count2 = config_svc.activate_category_for_ministere(str(ministere.id), cat.code)
    assert count1 == 1
    assert count2 == 0


def test_list_categories_with_active_roles(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """list_categories_with_active_roles retourne toutes les catégories du catalogue."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    cat, _ = config_svc.add_categorie_to_ministere(
        str(ministere.id), f"CatAll-{uuid4()}"
    )
    code = f"ALL{uuid4().hex[:4].upper()}"
    role, _ = config_svc.add_role_competence_to_categorie(cat.code, code, "Rôle All")
    config_svc.activate_role_for_ministere(str(ministere.id), role.code)

    cats_with_roles = config_svc.list_categories_with_active_roles(str(ministere.id))
    active_cats = {c.code for c, roles in cats_with_roles if roles}
    assert cat.code in active_cats


def test_ministere_role_config_unused(
    session: Session,
    config_svc: CampusConfigService,
    test_campus: Campus,
) -> None:
    """MinistereRoleConfig est importé et utilisé (pas unused import)."""
    ministere = _create_linked_ministere(session, config_svc, test_campus)
    role, _ = _setup_role(session, config_svc, test_campus)
    config_svc.activate_role_for_ministere(str(ministere.id), role.code)

    stmt = select(MinistereRoleConfig).where(
        MinistereRoleConfig.ministere_id == str(ministere.id),
        MinistereRoleConfig.role_code == role.code,
    )
    found = session.exec(stmt).first()
    assert found is not None
