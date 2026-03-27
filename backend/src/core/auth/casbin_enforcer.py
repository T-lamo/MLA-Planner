"""Casbin enforcer — moteur d'autorisation centralisé (RBAC with domains)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import casbin  # type: ignore[import-untyped]
from casbin_sqlalchemy_adapter import Adapter  # type: ignore[import-untyped]
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from conf.db.database import Database
from mla_enum import RoleName
from models.schema_db_model import AffectationRole

from .auth_utils import _affectation_valide, _role_name

CONF_PATH = os.path.join(os.path.dirname(__file__), "casbin_model.conf")

# Domaine universel pour les rôles sans scope ministère
WILDCARD_DOMAIN = "*"


@dataclass
class _EnforcerState:
    """Singleton mutable contenant l'enforcer après démarrage."""

    enforcer: Optional[casbin.Enforcer] = field(default=None)


_state = _EnforcerState()


def get_enforcer() -> Optional[casbin.Enforcer]:
    """Retourne l'enforcer courant (None si non initialisé)."""
    return _state.enforcer


def set_enforcer(enf: Optional[casbin.Enforcer]) -> None:
    """Injecte un enforcer (usage test uniquement)."""
    _state.enforcer = enf


def _add_default_policies(enf: casbin.Enforcer) -> None:
    """Seed les politiques par défaut pour chaque rôle métier."""
    policies: list[tuple[str, str, str, str]] = [
        (RoleName.SUPER_ADMIN.name, WILDCARD_DOMAIN, "*", "*"),
        (RoleName.ADMIN.name, WILDCARD_DOMAIN, "*", "*"),
        (RoleName.RESPONSABLE_MLA.name, WILDCARD_DOMAIN, "chants", "read"),
        (RoleName.RESPONSABLE_MLA.name, WILDCARD_DOMAIN, "chants", "write"),
        (RoleName.RESPONSABLE_MLA.name, WILDCARD_DOMAIN, "planning", "read"),
        (RoleName.RESPONSABLE_MLA.name, WILDCARD_DOMAIN, "planning", "write"),
        (RoleName.MEMBRE_MLA.name, WILDCARD_DOMAIN, "chants", "read"),
        (RoleName.MEMBRE_MLA.name, WILDCARD_DOMAIN, "planning", "read"),
    ]
    for role, dom, obj, act in policies:
        enf.add_policy(role, dom, obj, act)


def _add_groupings(enf: casbin.Enforcer, db: Session) -> None:
    """Convertit les AffectationRole actives en grouping policies Casbin.

    - Affectation sans contexte → g(user_id, role, '*').
    - Affectation avec contexte → g(user_id, role, ministere_id).
    """
    stmt = (
        select(AffectationRole)
        .options(selectinload(AffectationRole.role))  # type: ignore[arg-type]
        .options(selectinload(AffectationRole.contextes))  # type: ignore[arg-type]
    )
    affectations = db.exec(stmt).all()

    for aff in affectations:
        if not (aff.role and aff.role.libelle is not None):
            continue
        if not _affectation_valide(aff):
            continue

        role = _role_name(aff.role.libelle)

        # Grouping global '*' — permet l'accès aux ressources non scopées (chants…)
        enf.add_grouping_policy(aff.utilisateur_id, role, WILDCARD_DOMAIN)

        # Groupings scopés en plus, pour les vérifications par ministère
        for ctx in aff.contextes:
            if ctx.ministere_id and ctx.ministere_id != WILDCARD_DOMAIN:
                enf.add_grouping_policy(aff.utilisateur_id, role, ctx.ministere_id)


def build_enforcer(db: Session) -> None:
    """Construit et met en cache l'enforcer Casbin.

    À appeler une seule fois au démarrage (lifespan FastAPI).
    L'adaptateur SQLAlchemy crée la table casbin_rule si absente.
    """
    engine: Any = Database.get_engine()
    adapter: Any = Adapter(engine)
    enf: casbin.Enforcer = casbin.Enforcer(CONF_PATH, adapter)
    enf.clear_policy()
    _add_default_policies(enf)
    _add_groupings(enf, db)
    _state.enforcer = enf
