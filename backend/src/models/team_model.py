from typing import List

from pydantic import BaseModel, ConfigDict


class TeamMemberRead(BaseModel):
    """Membre léger avec ses rôles compétences."""

    id: str
    nom: str
    prenom: str
    roles: List[str]  # liste de role_code

    model_config = ConfigDict(from_attributes=True)


class TeamMinistereRead(BaseModel):
    """Ministère avec ses membres et leurs rôles."""

    id: str
    nom: str
    membres: List[TeamMemberRead]

    model_config = ConfigDict(from_attributes=True)


class CampusTeamRead(BaseModel):
    """Réponse complète : ministères du campus accessibles à l'utilisateur."""

    ministeres: List[TeamMinistereRead]

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "TeamMemberRead",
    "TeamMinistereRead",
    "CampusTeamRead",
]
