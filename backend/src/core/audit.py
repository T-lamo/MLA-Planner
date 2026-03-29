"""Module d'audit logging — trace les actions sensibles de l'application.

Format de chaque ligne :
  event=<event> user_id=<id> [key=value ...]

Configuration du logger "mla.audit" dans logging.ini pour rediriger
vers un fichier dédié ou un service externe en production.
"""

import logging
from typing import Any

_audit = logging.getLogger("mla.audit")


def audit(event: str, user_id: str | None = None, **kwargs: Any) -> None:
    """Enregistre une action auditée.

    Args:
        event: Identifiant de l'événement (ex: "login", "logout",
               "role_permissions_updated").
        user_id: ID de l'utilisateur à l'origine de l'action.
        **kwargs: Métadonnées supplémentaires (username, role_id, etc.).
    """
    parts = [f"event={event}", f"user_id={user_id or 'anonymous'}"]
    parts += [f"{k}={v}" for k, v in kwargs.items()]
    _audit.info(" ".join(parts))
