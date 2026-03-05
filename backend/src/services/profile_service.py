import logging
from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

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

    def create(self, data: ProfilCreateFull) -> ProfilReadFull:
        try:
            membre_in = MembreCreate(**data.model_dump(exclude={"utilisateur"}))
            db_membre = self.membre_svc.create(membre_in)

            if data.role_codes:
                self._sync_roles(db_membre, data.role_codes)

            user_payload = data.utilisateur.model_dump(exclude={"roles_ids"})
            user_payload["membre_id"] = db_membre.id

            db_user = Utilisateur(**user_payload)
            self.db.add(db_user)

            self.db.flush()
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
            membre_payload = MembreUpdate(
                **data.model_dump(exclude_unset=True, exclude={"utilisateur"})
            )
            self.membre_svc.update(identifiant, membre_payload)
            db_membre = self._get_db_obj(identifiant)

            # Sync des rôles si fournis
            if data.role_codes is not None:
                self._sync_roles(db_membre, data.role_codes)

            if data.utilisateur:
                if not db_membre.utilisateur:
                    # Utilisation de la nouvelle clé spécifique PROFIL
                    raise AppException(ErrorRegistry.PROFIL_USER_LINK_MISSING)

                user_update = data.utilisateur.model_dump(exclude_unset=True)
                for key, value in user_update.items():
                    setattr(db_membre.utilisateur, key, value)
                self.db.add(db_membre.utilisateur)

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
                    selectinload(cast(Any, Membre.utilisateur)),
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

    def list_all(self, campus_id: Optional[str] = None) -> List[ProfilReadFull]:
        try:
            statement = select(Membre).where(
                col(cast(Any, Membre.deleted_at))
                == None  # Noqa E711 # pylint: disable=singleton-comparison
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
