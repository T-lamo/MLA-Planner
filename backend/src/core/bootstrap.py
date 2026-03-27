import logging

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from core.auth.security import get_password_hash
from core.settings import settings
from mla_enum import RoleName  # noqa: F401 — conservé pour Casbin/auth
from models.schema_db_model import AffectationRole, Role, Utilisateur

logger = logging.getLogger(__name__)


def _get_or_create_superadmin_role(db: Session) -> Role:
    """Return the SUPER_ADMIN Role, creating it if absent."""
    role = db.exec(
        select(Role).where(Role.libelle == RoleName.SUPER_ADMIN.value)
    ).first()
    if role is None:
        role = Role(libelle=RoleName.SUPER_ADMIN.value)
        db.add(role)
        db.flush()
    return role


def bootstrap_superadmin(db: Session) -> None:
    """
    Crée l'utilisateur superadmin depuis les variables d'environnement.
    Idempotent : ne fait rien si l'utilisateur existe déjà.
    Ne met jamais à jour le mot de passe au redémarrage.
    """
    username = settings.SUPERADMIN_USERNAME
    password = settings.SUPERADMIN_PASSWORD

    if not password:
        logger.warning("SUPERADMIN_PASSWORD non défini — bootstrap superadmin ignoré.")
        return

    existing = db.exec(
        select(Utilisateur).where(Utilisateur.username == username)
    ).first()
    if existing:
        return

    try:
        role = _get_or_create_superadmin_role(db)
        user = Utilisateur(
            username=username,
            password=get_password_hash(password),
            actif=True,
            membre_id=None,
        )
        db.add(user)
        db.flush()
        db.add(AffectationRole(utilisateur_id=user.id, role_id=role.id))
        db.commit()
        logger.info("Superadmin '%s' créé avec succès.", username)
    except IntegrityError:
        db.rollback()
        # Race condition au premier déploiement — déjà créé par une autre instance
    except Exception:
        db.rollback()
        logger.error("Erreur lors du bootstrap superadmin.", exc_info=True)
        raise
