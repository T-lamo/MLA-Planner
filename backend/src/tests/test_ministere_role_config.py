"""
Tests pour MinistereRoleConfig (RC-158).

Vérifie la table t_ministere_role_config qui relie
un ministère à ses rôles compétences activés (catalogue global).
"""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from core.message import ErrorRegistry
from models.schema_db_model import (
    CategorieRole,
    Ministere,
    MinistereRoleConfig,
    RoleCompetence,
)

# pylint: disable=redefined-outer-name


# ------------------------------------------------------------------ #
#  Fixtures locales
# ------------------------------------------------------------------ #


@pytest.fixture
def ministere(session: Session) -> Ministere:
    """Ministère de test."""
    min_ = Ministere(
        nom=f"Ministere RC158 {uuid4()}",
        date_creation="2026-01-01",
        actif=True,
    )
    session.add(min_)
    session.flush()
    session.refresh(min_)
    return min_


@pytest.fixture
def categorie(session: Session) -> CategorieRole:
    """Catégorie de rôle globale (sans ministere_id)."""
    code = f"CAT_{str(uuid4())[:6].upper()}"
    cat = CategorieRole(
        code=code,
        libelle=f"Catégorie Test {code}",
    )
    session.add(cat)
    session.flush()
    session.refresh(cat)
    return cat


@pytest.fixture
def role(session: Session, categorie: CategorieRole) -> RoleCompetence:
    """Rôle compétence de test dans le catalogue global."""
    code = f"ROLE_{str(uuid4())[:6].upper()}"
    rc = RoleCompetence(
        code=code,
        libelle=f"Rôle Test {code}",
        categorie_code=categorie.code,
    )
    session.add(rc)
    session.flush()
    session.refresh(rc)
    return rc


# ------------------------------------------------------------------ #
#  Catalogue global : CategorieRole sans ministere_id
# ------------------------------------------------------------------ #


def test_categorie_role_has_no_ministere_id(categorie: CategorieRole) -> None:
    """CategorieRole ne doit plus avoir d'attribut ministere_id."""
    assert not hasattr(
        categorie, "ministere_id"
    ), "ministere_id ne doit plus exister sur CategorieRole (RC-158)"


def test_categorie_role_is_global(session: Session, categorie: CategorieRole) -> None:
    """Une CategorieRole est accessible sans filtrage par ministère."""
    stmt = select(CategorieRole).where(CategorieRole.code == categorie.code)
    result = session.exec(stmt).first()
    assert result is not None
    assert result.code == categorie.code


# ------------------------------------------------------------------ #
#  MinistereRoleConfig : liaison N:N
# ------------------------------------------------------------------ #


def test_create_ministere_role_config(
    session: Session,
    ministere: Ministere,
    role: RoleCompetence,
) -> None:
    """Crée un lien ministere-role et vérifie sa persistance."""
    config = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(config)
    session.flush()

    stmt = select(MinistereRoleConfig).where(
        MinistereRoleConfig.ministere_id == str(ministere.id),
        MinistereRoleConfig.role_code == role.code,
    )
    found = session.exec(stmt).first()
    assert found is not None
    assert found.ministere_id == str(ministere.id)
    assert found.role_code == role.code


def test_ministere_role_config_unique(
    session: Session,
    ministere: Ministere,
    role: RoleCompetence,
) -> None:
    """Un doublon (même ministere_id + role_code) lève une IntegrityError."""
    config1 = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(config1)
    session.flush()

    config2 = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(config2)
    with pytest.raises(IntegrityError):  # doublon PK composite
        session.flush()


def test_ministere_can_have_multiple_roles(
    session: Session,
    ministere: Ministere,
    categorie: CategorieRole,
) -> None:
    """Un ministère peut activer plusieurs rôles."""
    roles = []
    for i in range(3):
        code = f"MULTI_{str(uuid4())[:4].upper()}_{i}"
        rc = RoleCompetence(
            code=code,
            libelle=f"Rôle Multi {i}",
            categorie_code=categorie.code,
        )
        session.add(rc)
        session.flush()
        roles.append(rc)

    for rc in roles:
        cfg = MinistereRoleConfig(
            ministere_id=str(ministere.id),
            role_code=rc.code,
        )
        session.add(cfg)
    session.flush()

    stmt = select(MinistereRoleConfig).where(
        MinistereRoleConfig.ministere_id == str(ministere.id)
    )
    configs = list(session.exec(stmt).all())
    assert len(configs) == 3


def test_same_role_in_multiple_ministeres(
    session: Session,
    role: RoleCompetence,
) -> None:
    """Le même rôle peut être activé dans plusieurs ministères."""
    ministeres = []
    for _ in range(2):
        min_ = Ministere(
            nom=f"Ministere Multi {uuid4()}",
            date_creation="2026-01-01",
            actif=True,
        )
        session.add(min_)
        session.flush()
        session.refresh(min_)
        ministeres.append(min_)

    for min_ in ministeres:
        cfg = MinistereRoleConfig(
            ministere_id=str(min_.id),
            role_code=role.code,
        )
        session.add(cfg)
    session.flush()

    stmt = select(MinistereRoleConfig).where(MinistereRoleConfig.role_code == role.code)
    configs = list(session.exec(stmt).all())
    assert len(configs) == 2


def test_delete_ministere_cascades_config(
    session: Session,
    ministere: Ministere,
    role: RoleCompetence,
) -> None:
    """Supprimer un ministère efface ses configs (CASCADE)."""
    cfg = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(cfg)
    session.flush()

    session.delete(ministere)
    session.flush()
    session.expire_all()

    stmt = select(MinistereRoleConfig).where(
        MinistereRoleConfig.ministere_id == str(ministere.id)
    )
    assert session.exec(stmt).first() is None


def test_delete_role_cascades_config(
    session: Session,
    ministere: Ministere,
    role: RoleCompetence,
) -> None:
    """Supprimer un rôle efface ses configs (CASCADE)."""
    cfg = MinistereRoleConfig(
        ministere_id=str(ministere.id),
        role_code=role.code,
    )
    session.add(cfg)
    session.flush()

    session.delete(role)
    session.flush()
    session.expire_all()

    stmt = select(MinistereRoleConfig).where(MinistereRoleConfig.role_code == role.code)
    assert session.exec(stmt).first() is None


# ------------------------------------------------------------------ #
#  ErrorRegistry : nouveaux codes RC-158
# ------------------------------------------------------------------ #


def test_error_registry_minst_role_already_active() -> None:
    """MINST_ROLE_ALREADY_ACTIVE est défini avec le bon code."""
    err = ErrorRegistry.MINST_ROLE_ALREADY_ACTIVE
    assert err.code == "ROLE_006"
    assert err.http_status == 409


def test_error_registry_minst_role_not_found() -> None:
    """MINST_ROLE_NOT_FOUND est défini avec le bon code."""
    err = ErrorRegistry.MINST_ROLE_NOT_FOUND
    assert err.code == "ROLE_007"
    assert err.http_status == 404
