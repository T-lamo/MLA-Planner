"""Utilitaires partagés entre auth_dependencies et casbin_enforcer.

Isolés ici pour éviter le cycle d'import circulaire :
auth_dependencies → casbin_enforcer → auth_dependencies.
"""

from datetime import date
from enum import Enum

from mla_enum import RoleName


def _role_name(libelle: object) -> str:
    """Normalise un libellé de rôle en nom d'enum (ex: 'SUPER_ADMIN')."""
    if isinstance(libelle, RoleName):
        return libelle.name
    if isinstance(libelle, Enum):
        return libelle.name
    return str(libelle)


def _affectation_valide(aff: object) -> bool:
    """True si l'affectation est active et dans sa fenêtre de validité."""
    today = date.today()
    return (
        bool(getattr(aff, "active", True))
        and (
            getattr(aff, "dateDebut", None) is None
            or getattr(aff, "dateDebut") <= today
        )
        and (getattr(aff, "dateFin", None) is None or getattr(aff, "dateFin") >= today)
    )
