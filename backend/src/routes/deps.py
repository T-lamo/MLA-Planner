from fastapi import Depends

from core.auth.auth_dependencies import RoleChecker

# Instance réutilisable pour le checker
admin_only = Depends(RoleChecker(["ADMIN"]))

# Configuration standard des accès CRUD
STANDARD_ADMIN_ONLY_DEPS = {
    "create": [admin_only],
    "update": [admin_only],
    "delete": [admin_only],
    "read": [],  # Public
}
