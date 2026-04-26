from fastapi import Depends

from core.auth.auth_dependencies import CapabilityChecker

# Instance réutilisable pour le checker
admin_only = Depends(CapabilityChecker(["CAMPUS_ADMIN"]))
super_admin_only = Depends(CapabilityChecker(["SYSTEM_MANAGE"]))

# Configuration standard des accès CRUD
STANDARD_ADMIN_ONLY_DEPS = {
    "create": [admin_only],
    "update": [admin_only],
    "delete": [admin_only],
    "read": [],  # Public
}

# Accès réservé au Super Admin (bootstrap : orgs, campuses)
SUPER_ADMIN_ONLY_DEPS = {
    "create": [super_admin_only],
    "update": [super_admin_only],
    "delete": [super_admin_only],
    "read": [],  # Public
}
