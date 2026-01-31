import os

SEED_ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME", "admin")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

if not SEED_ADMIN_PASSWORD:
    raise RuntimeError("SEED_ADMIN_PASSWORD doit être défini dans l'environnement")

LOGGING_ENABLED = True
