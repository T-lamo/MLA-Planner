import logging
from typing import Any, List, Optional, cast

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from core.exceptions import NotFoundException
from models import (
    Campus,
    Membre,
    MembreCreate,
    MembreUpdate,
    ProfilCreateFull,
    ProfilReadFull,
    ProfilUpdateFull,
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

    def create(self, data: ProfilCreateFull) -> ProfilReadFull:
        try:
            membre_in = MembreCreate(**data.model_dump(exclude={"utilisateur"}))
            db_membre = self.membre_svc.create(membre_in)

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
            raise e

    # Fix W0237: Renommage de item_id en identifiant pour respecter BaseService
    def update(self, identifiant: str, data: ProfilUpdateFull) -> ProfilReadFull:
        try:
            membre_payload = MembreUpdate(
                **data.model_dump(exclude_unset=True, exclude={"utilisateur"})
            )
            self.membre_svc.update(identifiant, membre_payload)

            if data.utilisateur:
                db_membre = self._get_db_obj(identifiant)
                if not db_membre.utilisateur:
                    raise NotFoundException("L'utilisateur associé n'existe pas.")

                user_update = data.utilisateur.model_dump(exclude_unset=True)
                for key, value in user_update.items():
                    setattr(db_membre.utilisateur, key, value)
                self.db.add(db_membre.utilisateur)

            self.db.commit()
            return self.get_one(identifiant)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur update profil {identifiant}: {str(e)}")
            raise e

    # Fix W0237: Signature cohérente avec BaseService
    def get_one(self, identifiant: str) -> ProfilReadFull:
        db_obj = self._get_db_obj(identifiant)
        return ProfilReadFull.model_validate(db_obj)

    # Fix W0237: Signature cohérente avec BaseService
    def delete(self, identifiant: str) -> None:
        try:
            self.membre_svc.delete(identifiant)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def _get_db_obj(self, identifiant: str) -> Membre:
        statement = (
            select(Membre)
            .where(Membre.id == identifiant)
            .options(
                selectinload(cast(Any, Membre.utilisateur)),
                selectinload(cast(Any, Membre.campuses)),
                selectinload(cast(Any, Membre.ministeres)),
                selectinload(cast(Any, Membre.poles)),
                selectinload(cast(Any, Membre.roles_assoc)),
            )
        )
        result = self.db.exec(statement).unique().first()
        if not result:
            raise NotFoundException(f"Profil {identifiant} introuvable.")
        return result

    def list_paginated(
        self, limit: int, offset: int, campus_id: Optional[str] = None
    ) -> PaginatedResponse[ProfilReadFull]:
        items = self.membre_svc.repo.get_paginated(limit, offset, campus_id=campus_id)
        total = self.membre_svc.repo.count(campus_id=campus_id)

        data = [ProfilReadFull.model_validate(item) for item in items]
        return PaginatedResponse(total=total, limit=limit, offset=offset, data=data)

    def list_all(self, campus_id: Optional[str] = None) -> List[ProfilReadFull]:
        # Fix E1101: cast Any pour éviter l'erreur no-member sur FieldInfo
        statement = select(Membre).where(
            col(cast(Any, Membre.deleted_at)) == None  # Noqa E711
        )  # Noqa E711

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
