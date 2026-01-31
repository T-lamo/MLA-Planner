import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from core.auth.security import get_password_hash
from models import AffectationRole, Permission, Role, RolePermission, Utilisateur

from .seed.data import PERMISSIONS, ROLES
from .seed.exceptions import SeedIntegrityError


class SeedService:
    """
    Service de seed RBAC
    - Idempotent
    - Transactionnel
    - Testable
    - Sécurisé
    """

    def __init__(self, db: Session, logger: logging.Logger | None = None):
        self.db = db
        self.logger = logger or logging.getLogger("rbac_seed")

    # ==========================
    # PUBLIC ENTRYPOINT
    # ==========================
    def run(self):
        self.logger.info("🌱 Démarrage seed RBAC")

        try:
            with self.db.begin():
                role_map = self._seed_roles()
                perm_map = self._seed_permissions()
                self._seed_role_permissions(role_map, perm_map)
                self._seed_users_for_roles(role_map)

            self.logger.info("✅ Seed RBAC terminé avec succès")

        except SQLAlchemyError as e:
            self.logger.error("❌ Erreur SQL pendant le seed", exc_info=True)
            raise SeedIntegrityError("Erreur DB pendant le seed RBAC") from e

    # ==========================
    # UTILS
    # ==========================
    def _get_or_create(self, model, defaults=None, **filters):
        stmt = select(model).filter_by(**filters)
        instance = self.db.exec(stmt).first()

        if instance:
            return instance, False

        obj = model(**filters, **(defaults or {}))
        self.db.add(obj)
        return obj, True

    # ==========================
    # ROLES
    # ==========================
    def _seed_roles(self):
        self.logger.info("Seeding roles...")
        role_map = {}

        for role_name in ROLES:
            role, created = self._get_or_create(Role, libelle=role_name)

            role_map[role_name] = role

            if created:
                self.logger.info(f"Role créé: {role_name}")

        self.db.flush()
        return role_map

    # ==========================
    # PERMISSIONS
    # ==========================
    def _seed_permissions(self):
        self.logger.info("Seeding permissions...")
        perm_map = {}

        all_permissions = {p for perms in PERMISSIONS.values() for p in perms}

        for code in all_permissions:
            perm, created = self._get_or_create(
                Permission, code=code, defaults={"description": f"Permission {code}"}
            )

            perm_map[code] = perm

            if created:
                self.logger.info(f"Permission créée: {code}")

        self.db.flush()
        return perm_map

    # ==========================
    # ROLE ↔ PERMISSIONS
    # ==========================
    def _seed_role_permissions(self, role_map, perm_map):
        self.logger.info("Assignation permissions aux rôles...")

        for role_name, permissions in PERMISSIONS.items():
            role = role_map.get(role_name)

            if not role:
                raise SeedIntegrityError(f"Rôle manquant: {role_name}")

            for perm_code in permissions:
                perm = perm_map.get(perm_code)

                if not perm:
                    raise SeedIntegrityError(f"Permission manquante: {perm_code}")

                exists = self.db.exec(
                    select(RolePermission)
                    .where(RolePermission.role_id == role.id)
                    .where(RolePermission.permission_id == perm.id)
                ).first()

                if not exists:
                    self.db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    # ==========================
    # ADMIN
    # ==========================
    def _seed_users_for_roles(self, role_map):
        """
        Crée un utilisateur pour chaque rôle défini dans `ROLES`.
        Idempotent : ne recrée pas les utilisateurs existants.
        Assigne le rôle correspondant si non déjà assigné.
        """
        self.logger.info("Création d'un utilisateur par rôle...")

        for role_name, role in role_map.items():
            username = f"user_{role_name.lower()}"  # Génère un username unique pour chaque rôle
            password = get_password_hash(
                "ChangeMe123!"
            )  # Mot de passe par défaut à changer

            # Création ou récupération de l'utilisateur
            user, created = self._get_or_create(
                Utilisateur,
                username=username,
                defaults={"password": password, "actif": True},
            )

            if created:
                self.logger.info(
                    "Utilisateur créé pour le rôle %s: %s", role_name, username
                )

            else:
                self.logger.info(
                    "Utilisateur déjà existant pour le rôle  %s: %s",
                    role_name,
                    username,
                )

            # Vérification si le rôle est déjà assigné
            exists = self.db.exec(
                select(AffectationRole)
                .where(AffectationRole.utilisateur_id == user.id)
                .where(AffectationRole.role_id == role.id)
            ).first()

            if not exists:
                self.db.add(
                    AffectationRole(
                        utilisateur_id=user.id, role_id=role.id, active=True
                    )
                )
                self.logger.info(
                    "Rôle %s assigné à l'utilisateur %s", role_name, username
                )

        # ==========================

    # CONFIG SAFE
    # ==========================
    def _get_admin_username(self):
        # pylint: disable=import-outside-toplevel
        from .seed.config import SEED_ADMIN_USERNAME

        return SEED_ADMIN_USERNAME

    def _get_admin_password(self):
        # pylint: disable=import-outside-toplevel
        from .seed.config import SEED_ADMIN_PASSWORD

        if not SEED_ADMIN_PASSWORD:
            raise SeedIntegrityError("SEED_ADMIN_PASSWORD non défini")

        return SEED_ADMIN_PASSWORD
