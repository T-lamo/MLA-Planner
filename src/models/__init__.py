from typing import List

from .activite_model import *
from .activite_model import __all__ as activite
from .affectation_context_model import *
from .affectation_context_model import __all__ as affectation_context
from .affectation_role_model import *
from .affectation_role_model import __all__ as affectation_role
from .chantre_model import *
from .chantre_model import __all__ as chantre
from .membre_model import *
from .membre_model import __all__ as membres
from .ministere_model import *
from .ministere_model import __all__ as ministre_model
from .permission_model import *
from .permission_model import __all__ as permission_model
from .pole_model import *
from .pole_model import __all__ as pole_model
from .role_model import *
from .role_model import __all__ as roles
from .schema_db_model import *
from .schema_db_model import __all__ as schema_dbs
from .utilisateur_model import *
from .utilisateur_model import __all__ as utilisateurs
from .voix_model import *
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
    + list(ministre_model)
    + list(permission_model)
    + list(pole_model)
    + list(voix_model)
    + list(chantre)
)
