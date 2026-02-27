from typing import List

from .activite_model import *  # noqa: F401,F403
from .activite_model import __all__ as activite
from .affectation_context_model import *  # noqa: F401,F403
from .affectation_context_model import __all__ as affectation_context
from .affectation_model import *  # noqa: F401,F403
from .affectation_model import __all__ as affectation
from .affectation_role_model import *  # noqa: F401,F403
from .affectation_role_model import __all__ as affectation_role
from .base_pagination import *  # noqa: F401,F403
from .campus_model import *  # noqa: F401,F403
from .campus_model import __all__ as campus
from .categorie_role_model import *  # noqa: F401,F403
from .categorie_role_model import __all__ as category_role
from .equipe_membre import *  # noqa: F401,F403
from .equipe_membre import __all__ as equipe_membre
from .equipe_model import *  # noqa: F401,F403
from .equipe_model import __all__ as equipe
from .indisponibilite_model import *  # noqa: F401,F403
from .indisponibilite_model import __all__ as indisponibilite
from .membre_model import *  # noqa: F401,F403
from .membre_model import __all__ as membres
from .membre_role_model import *  # noqa: F401,F403
from .membre_role_model import __all__ as membre_role
from .ministere_model import *  # noqa: F401,F403
from .ministere_model import __all__ as ministere
from .organisationicc_model import *  # noqa: F401,F403
from .organisationicc_model import __all__ as organisation
from .pays_model import *  # noqa: F401,F403
from .pays_model import __all__ as pays
from .permission_model import *  # noqa: F401,F403
from .permission_model import __all__ as permission_model
from .planning_model import *  # noqa: F401,F403
from .planning_model import __all__ as planning_model
from .pole_model import *  # noqa: F401,F403
from .pole_model import __all__ as pole_model
from .profil_model import *  # noqa: F401,F403
from .profil_model import __all__ as profile
from .role_competence_model import *  # noqa: F401,F403
from .role_competence_model import __all__ as role_competence
from .role_model import *  # noqa: F401,F403
from .role_model import __all__ as roles
from .schema_db_model import *  # noqa: F401,F403
from .schema_db_model import __all__ as schema_dbs
from .slot_model import *  # noqa: F401,F403
from .slot_model import __all__ as slot_model
from .utilisateur_model import *  # noqa: F401,F403
from .utilisateur_model import __all__ as utilisateurs
from .voix_model import *  # noqa: F401,F403
from .voix_model import __all__ as voix_model

# N'oublie pas d'importer ton nouveau modèle ici si tu l'as déjà créé
# from .token_blacklist_model import *
# from .token_blacklist_model import __all__ as blacklist

__all__: List[str] = (
    list(roles)
    + list(utilisateurs)
    + list(membres)
    + list(schema_dbs)
    + list(activite)
    + list(affectation_context)
    + list(affectation_role)
    + list(ministere)
    + list(permission_model)
    + list(pole_model)
    + list(voix_model)
    + list(organisation)
    + list(pays)
    + list(campus)
    + list(category_role)
    + list(role_competence)
    + list(membre_role)
    + list(indisponibilite)
    + list(equipe)
    + list(equipe_membre)
    + list(slot_model)
    + list(planning_model)
    + list(affectation)
    + list(profile)
)
