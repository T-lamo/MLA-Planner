from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Organisation, OrganisationCreate
from models.organisation_model import OrganisationRead, OrganisationUpdate
from repositories.organisation_repository import OrganisationRepository

from .base_service import BaseService


class OrganisationService(
    BaseService[
        OrganisationCreate,
        OrganisationRead,
        OrganisationUpdate,
        Organisation,
    ]
):
    def __init__(self, db: Session):
        super().__init__(repo=OrganisationRepository(db), resource_name="Organisation")

    def create(self, data: OrganisationCreate) -> Organisation:
        # Logique spécifique : vérification du nom unique
        if self.repo.get_by_nom(data.nom):
            raise AppException(ErrorRegistry.ORG_DUPLICATE, nom=data.nom)

        org = Organisation(**data.model_dump())
        try:
            return self.repo.create(org)
        except IntegrityError as exc:
            raise AppException(ErrorRegistry.CORE_INTEGRITY_ERROR) from exc

    def update(self, identifiant: str, data: OrganisationUpdate) -> Organisation:
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Logique spécifique : vérification du nom si modifié
        if "nom" in update_data and update_data["nom"] != obj.nom:
            if self.repo.get_by_nom(update_data["nom"]):
                raise AppException(ErrorRegistry.ORG_DUPLICATE, nom=update_data["nom"])

        try:
            return self.repo.update(obj, update_data)
        except Exception as exc:
            raise AppException(ErrorRegistry.CORE_INTEGRITY_ERROR) from exc
