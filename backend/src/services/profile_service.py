import logging
from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from core.auth.security import get_password_hash
from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import (
    Campus,
    Membre,
    MembreCreate,
    MembreRole,
    MembreUpdate,
    ProfilCreateFull,
    ProfilReadFull,
    ProfilUpdateFull,
    RoleCompetence,
    Utilisateur,
)
from models.base_pagination import PaginatedResponse
from models.ministere_model import MinistereSimple
from models.schema_db_model import (
    AffectationRole,
    CampusMinistereLink,
    MembreCampusLink,
    MembreMinistereLink,
)
from repositories.membre_repository import _exclude_superadmin_clause
from services.membre_service import MembreService

from .base_service import BaseService

logger = logging.getLogger(__name__)


class ProfileService(
    BaseService[ProfilCreateFull, ProfilReadFull, ProfilUpdateFull, ProfilReadFull]
):
    def __init__(self, db: Session):
        self.db = db
        self.membre_svc = MembreService(db)
        # Fix W0231: Appel du constructeur parent avec le repo adéquat
        super().__init__(repo=self.membre_svc.repo, resource_name="Profile")

    def _resolve_campus_principal(
        self,
        campus_ids: List[str],
        campus_principal_id: Optional[str],
        strict: bool = True,
    ) -> Optional[str]:
        """Validate/auto-assign campus_principal_id against campus_ids.

        strict=True  → raise if campus_principal_id not in campus_ids
        (explicit user input).
        strict=False → auto-clear if campus_principal_id
        not in campus_ids (inherited value).
        Auto-assigns if campus_ids has exactly one element
          and no principal set.
        """
        if campus_principal_id:
            if campus_principal_id in campus_ids:
                return campus_principal_id
            if strict:
                raise AppException(ErrorRegistry.PROFIL_CAMPUS_PRINCIPAL_INVALID)
            # Not strict: campus was removed, fall through to auto-assign logic
        if len(campus_ids) == 1:
            return campus_ids[0]
        return None

    def _sync_roles(self, membre: Membre, role_codes: List[str]):
        """
        Gère le différentiel des rôles (Ajout/Suppression) pour un membre.
        """
        # 1. Vérifier l'existence des rôles demandés
        if role_codes:
            stmt = select(RoleCompetence).where(
                col(RoleCompetence.code).in_(role_codes)
            )
            db_roles = self.db.exec(stmt).all()
            if len(db_roles) != len(role_codes):
                found_codes = [r.code for r in db_roles]
                missing = list(set(role_codes) - set(found_codes))
                raise AppException(ErrorRegistry.ROLE_NOT_FOUND, missing=missing)

        # 2. Récupérer les rôles actuels
        current_roles_map = {ra.role_code: ra for ra in membre.roles_assoc}
        new_codes = set(role_codes)
        old_codes = set(current_roles_map.keys())

        # Supprimer les rôles retirés
        for code in old_codes - new_codes:
            self.db.delete(current_roles_map[code])

        # Ajouter les nouveaux rôles
        for code in new_codes - old_codes:
            new_assoc = MembreRole(membre_id=membre.id, role_code=code)
            self.db.add(new_assoc)

    def _sync_utilisateur_roles(
        self, utilisateur: Utilisateur, roles_ids: List[str]
    ) -> None:
        """Synchronise les AffectationRole (rôles applicatifs) d'un utilisateur."""
        # Supprimer les affectations existantes
        existing = self.db.exec(
            select(AffectationRole).where(
                AffectationRole.utilisateur_id == utilisateur.id
            )
        ).all()
        for aff in existing:
            self.db.delete(aff)
        # Créer les nouvelles affectations
        for role_id in roles_ids:
            self.db.add(AffectationRole(utilisateur_id=utilisateur.id, role_id=role_id))

    def create(self, data: ProfilCreateFull) -> ProfilReadFull:
        try:
            membre_data = data.model_dump(exclude={"utilisateur"})
            membre_data["campus_principal_id"] = self._resolve_campus_principal(
                data.campus_ids, data.campus_principal_id
            )
            membre_in = MembreCreate(**membre_data)
            db_membre = self.membre_svc.create(membre_in)

            if data.role_codes:
                self._sync_roles(db_membre, data.role_codes)

            user_payload = data.utilisateur.model_dump(exclude={"roles_ids"})
            user_payload["membre_id"] = db_membre.id

            if user_payload.get("password"):
                user_payload["password"] = get_password_hash(user_payload["password"])

            db_user = Utilisateur(**user_payload)
            self.db.add(db_user)
            self.db.flush()  # pour obtenir db_user.id

            roles_ids = data.utilisateur.roles_ids or []
            if roles_ids:
                self._sync_utilisateur_roles(db_user, roles_ids)

            self.db.commit()
            logger.info(f"Profil créé avec succès : {db_membre.email}")

            return self.get_one(db_membre.id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Échec de la création du profil : {str(e)}")
            raise AppException(
                ErrorRegistry.CORE_ACTION_IMPOSSIBLE, resource="Profile"
            ) from e

    def update(self, identifiant: str, data: ProfilUpdateFull) -> ProfilReadFull:
        try:
            raw = data.model_dump(exclude_unset=True, exclude={"utilisateur"})

            # Re-validate campus_principal_id if campuses or principal changed
            if "campus_ids" in raw or "campus_principal_id" in raw:
                current = self._get_db_obj(identifiant)
                effective_ids = raw.get("campus_ids", [c.id for c in current.campuses])
                desired_principal = raw.get(
                    "campus_principal_id", current.campus_principal_id
                )
                # strict only when caller explicitly set campus_principal_id
                strict = "campus_principal_id" in raw
                raw["campus_principal_id"] = self._resolve_campus_principal(
                    effective_ids, desired_principal, strict=strict
                )

            membre_payload = MembreUpdate(**raw)
            self.membre_svc.update(identifiant, membre_payload)
            db_membre = self._get_db_obj(identifiant)

            # Sync des rôles si fournis
            if data.role_codes is not None:
                self._sync_roles(db_membre, data.role_codes)

            if data.utilisateur:
                if not db_membre.utilisateur:
                    raise AppException(ErrorRegistry.PROFIL_USER_LINK_MISSING)

                user_update = data.utilisateur.model_dump(
                    exclude_unset=True, exclude={"roles_ids"}
                )
                for key, value in user_update.items():
                    if key == "password" and value:
                        value = get_password_hash(value)
                    setattr(db_membre.utilisateur, key, value)
                self.db.add(db_membre.utilisateur)

                roles_ids = data.utilisateur.roles_ids
                if roles_ids is not None:
                    self._sync_utilisateur_roles(db_membre.utilisateur, roles_ids)

            self.db.commit()
            return self.get_one(identifiant)
        except AppException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur update profil {identifiant}: {str(e)}")
            raise AppException(
                ErrorRegistry.CORE_ACTION_IMPOSSIBLE, resource="Profile"
            ) from e

    def get_one(self, identifiant: str) -> ProfilReadFull:
        db_obj = self._get_db_obj(identifiant)
        return ProfilReadFull.model_validate(db_obj)

    def delete(self, identifiant: str) -> None:
        try:
            self.membre_svc.delete(identifiant)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Échec de la suppression du profil {identifiant}: {str(e)}")
            raise AppException(
                ErrorRegistry.CORE_ACTION_IMPOSSIBLE, resource="Profile"
            ) from e

    def _get_db_obj(self, identifiant: str) -> Membre:
        try:
            statement = (
                select(Membre)
                .where(Membre.id == identifiant)
                .options(
                    selectinload(cast(Any, Membre.utilisateur))
                    .selectinload(cast(Any, Utilisateur.affectations))
                    .selectinload(cast(Any, AffectationRole.role)),
                    selectinload(cast(Any, Membre.campuses)),
                    selectinload(cast(Any, Membre.ministeres)),
                    selectinload(cast(Any, Membre.poles)),
                    selectinload(cast(Any, Membre.roles_assoc))
                    .selectinload(cast(Any, MembreRole.role))
                    .selectinload(cast(Any, RoleCompetence.categorie)),
                )
            )
            result = self.db.exec(statement).unique().first()
            if not result:
                # Utilisation du domaine spécifique PROFIL avec l'id
                raise AppException(ErrorRegistry.PROFIL_NOT_FOUND, id=identifiant)
            return result
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Erreur technique lors de la récupération du profil : {e}")
            raise AppException(ErrorRegistry.CORE_DATABASE_ERROR) from e

    def list_paginated(
        self, limit: int, offset: int, campus_id: Optional[str] = None
    ) -> PaginatedResponse[ProfilReadFull]:
        try:
            items = self.membre_svc.repo.get_paginated(
                limit, offset, campus_id=campus_id
            )
            total = self.membre_svc.repo.count(campus_id=campus_id)

            data = [ProfilReadFull.model_validate(item) for item in items]
            return PaginatedResponse(total=total, limit=limit, offset=offset, data=data)
        except Exception as e:
            logger.error(f"Erreur list_paginated: {e}")
            raise AppException(ErrorRegistry.PROFIL_DATA_ERROR) from e

    def get_my_ministeres_by_campus(
        self, membre_id: str, campus_id: str
    ) -> List[MinistereSimple]:
        """Ministères de l'utilisateur filtrés sur un campus donné."""
        profil = self.get_one(membre_id)
        stmt = select(CampusMinistereLink).where(
            CampusMinistereLink.campus_id == campus_id
        )
        links = self.db.exec(stmt).all()
        campus_min_ids = {lnk.ministere_id for lnk in links}
        return [
            MinistereSimple.model_validate(m)
            for m in profil.ministeres
            if m.id in campus_min_ids
        ]

    def list_by_ministere(
        self,
        ministere_id: str,
        *,
        requesting_membre_id: Optional[str] = None,
        bypass_check: bool = False,
        campus_id: Optional[str] = None,
    ) -> List[ProfilReadFull]:
        """Membres liés à un ministère donné, optionnellement filtrés par campus.

        bypass_check=True pour les admins (CAMPUS_ADMIN).
        Sinon, requesting_membre_id doit appartenir au ministère.
        campus_id filtre les résultats sur un campus spécifique.
        """
        if not bypass_check:
            if not requesting_membre_id:
                raise AppException(ErrorRegistry.PROFIL_MINISTERE_ACCESS_DENIED)
            membre = self._get_db_obj(requesting_membre_id)
            if not any(m.id == ministere_id for m in membre.ministeres):
                raise AppException(ErrorRegistry.PROFIL_MINISTERE_ACCESS_DENIED)
        try:
            statement = (
                select(Membre)
                .join(
                    MembreMinistereLink,
                    cast(Any, MembreMinistereLink.membre_id == Membre.id),
                )
                .where(MembreMinistereLink.ministere_id == ministere_id)
                .where(col(cast(Any, Membre.deleted_at)) == None)  # noqa: E711
            )
            if campus_id:
                statement = statement.join(
                    MembreCampusLink,
                    cast(Any, MembreCampusLink.membre_id == Membre.id),
                ).where(MembreCampusLink.campus_id == campus_id)
            statement = statement.options(
                selectinload(cast(Any, Membre.utilisateur)),
                selectinload(cast(Any, Membre.campuses)),
            ).distinct()
            items = self.db.exec(statement).unique().all()
            return [ProfilReadFull.model_validate(i) for i in items]
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Erreur list_by_ministere: {e}")
            raise AppException(ErrorRegistry.CORE_DATABASE_ERROR) from e

    def list_all(self, campus_id: Optional[str] = None) -> List[ProfilReadFull]:
        try:
            statement = select(Membre).where(
                col(cast(Any, Membre.deleted_at)) == None,  # noqa: E711
                _exclude_superadmin_clause(),
            )

            if campus_id:
                statement = statement.join(cast(Any, Membre.campuses)).where(
                    Campus.id == campus_id
                )

            statement = statement.options(
                selectinload(cast(Any, Membre.utilisateur)),
                selectinload(cast(Any, Membre.campuses)),
            ).distinct()

            items = self.db.exec(statement).unique().all()
            return [ProfilReadFull.model_validate(i) for i in items]
        except Exception as e:
            logger.error(f"Erreur list_all: {e}")
            raise AppException(ErrorRegistry.CORE_DATABASE_ERROR) from e
