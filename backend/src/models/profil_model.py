from typing import Dict, List, Optional, Sequence

from pydantic import computed_field

# Importation des modèles de base et de lecture optimisés
from .campus_model import CampusRead
from .membre_model import (
    MembreCreate,
    MembreRead,
    MembreRoleRich,
    MembreUpdate,
    UtilisateurSimple,
)
from .ministere_model import MinistereRead
from .pole_model import PoleRead
from .role_competence_model import RoleCompetenceRead
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
    roles_assoc: Sequence[MembreRoleRich] = []
    # Relations N:N (Surcharge pour utiliser les versions allégées)
    campuses: List[CampusRead] = []
    ministeres: List[MinistereRead] = []
    poles: List[PoleRead] = []

    @computed_field
    def competences_par_categorie(self) -> Dict[str, List[RoleCompetenceRead]]:
        """
        Transforme la relation plate roles_assoc en dictionnaire groupé par catégorie.
        """
        grouped: Dict[str, List[RoleCompetenceRead]] = {}
        for assoc in self.roles_assoc:
            # On accède au rôle via l'association MembreRole
            if hasattr(assoc, "role") and assoc.role:
                role_data = assoc.role
                cat_name = (
                    role_data.categorie.libelle if role_data.categorie else "Autres"
                )

                if cat_name not in grouped:
                    grouped[cat_name] = []
                grouped[cat_name].append(RoleCompetenceRead.model_validate(role_data))
        return grouped

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
    role_codes: List[str] = []


# ---------------------------------------------------------
# 3. UPDATE FULL
# ---------------------------------------------------------
class ProfilUpdateFull(MembreUpdate):
    """
    Permet la mise à jour partielle des infos membres, des relations (IDs)
    et des informations de compte utilisateur.
    """

    utilisateur: Optional[UtilisateurUpdate] = None
    role_codes: List[str] = []


__all__ = [
    "ProfilReadFull",
    "ProfilCreateFull",
    "ProfilUpdateFull",
]
