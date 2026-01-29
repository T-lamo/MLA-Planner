import importlib
from typing import List

from .activite_model import *
from .activite_model import __all__ as activite
from .affectation_context_model import *
from .affectation_context_model import __all__ as affectation_context
from .affectation_role_model import *
from .affectation_role_model import __all__ as affectation_role
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

__all__: List[str] = (
    roles
    + utilisateurs
    + membres
    + schema_dbs
    + activite
    + affectation_context
    + affectation_role
    + ministre_model
    + permission_model
    + pole_model
    + voix_model
)
