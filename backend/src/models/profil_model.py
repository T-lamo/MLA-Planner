from typing import List, Optional

# Importation des modèles de base et de lecture optimisés
from .campus_model import CampusRead
from .membre_model import (
    MembreCreate,
    MembreRead,
    MembreRoleSimple,
    MembreUpdate,
    UtilisateurSimple,
)
from .ministere_model import MinistereRead
from .pole_model import PoleRead
from .utilisateur_model import UtilisateurCreate, UtilisateurUpdate


# ---------------------------------------------------------
# 1. READ FULL (Version d'exportation finale et allégée)
# ---------------------------------------------------------
class ProfilReadFull(MembreRead):
    """
    Version d'exportation riche et performante.
    Utilise les versions 'Read' optimisées pour stopper la récursion :
    - MinistereRead ne contient plus de membres.
    - PoleRead ne contient plus de membres.
    - UtilisateurSimple/MembreRoleSimple ne contiennent plus de membre_id.
    """

    utilisateur: Optional[UtilisateurSimple] = None
    roles_assoc: List[MembreRoleSimple] = []
    # Relations N:N (Surcharge pour utiliser les versions allégées)
    campuses: List[CampusRead] = []
    ministeres: List[MinistereRead] = []
    poles: List[PoleRead] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------
# 2. CREATE FULL
# ---------------------------------------------------------
class ProfilCreateFull(MembreCreate):
    """
    Hérite de MembreCreate (inclut campus_ids, ministere_ids, pole_ids).
    Ajoute l'objet de création utilisateur pour l'atomicité.
    """

    utilisateur: UtilisateurCreate


# ---------------------------------------------------------
# 3. UPDATE FULL
# ---------------------------------------------------------
class ProfilUpdateFull(MembreUpdate):
    """
    Permet la mise à jour partielle des infos membres, des relations (IDs)
    et des informations de compte utilisateur.
    """

    utilisateur: Optional[UtilisateurUpdate] = None


__all__ = [
    "ProfilReadFull",
    "ProfilCreateFull",
    "ProfilUpdateFull",
]
