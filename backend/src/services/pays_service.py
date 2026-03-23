from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Pays, PaysCreate
from models.pays_model import PaysRead, PaysUpdate
from repositories.organisation_repository import OrganisationRepository
from repositories.pays_repository import PaysRepository
from services.base_service import BaseService


class PaysService(BaseService[PaysCreate, PaysRead, PaysUpdate, Pays]):
    def __init__(self, db: Session):
        super().__init__(repo=PaysRepository(db), resource_name="Pays")
        self.org_repo = OrganisationRepository(db)

    def create(self, data: PaysCreate) -> Pays:
        # Validation spécifique : L'organisation parente doit exister
        if not self.org_repo.get_by_id(data.organisation_id):
            raise AppException(ErrorRegistry.ORG_NOT_FOUND)

        pays = Pays(**data.model_dump())
        try:
            return self.repo.create(pays)
        except IntegrityError as exc:
            raise AppException(ErrorRegistry.PAYS_DUPLICATE) from exc

    def update(self, identifiant: str, data: PaysUpdate) -> Pays:
        pays_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Validation spécifique : vérifier la nouvelle organisation si fournie
        if "organisation_id" in update_data:
            if not self.org_repo.get_by_id(update_data["organisation_id"]):
                raise AppException(ErrorRegistry.ORG_NOT_FOUND)

        try:
            return self.repo.update(pays_db, update_data)
        except Exception as exc:
            raise AppException(ErrorRegistry.PAYS_DUPLICATE) from exc
