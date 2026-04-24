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

    def _validate_parent(self, parent_id: str, org_id: str | None = None) -> None:
        """Vérifie que parent_id existe et n'est pas l'organisation elle-même."""
        parent = self.repo.get_by_id(parent_id)
        if not parent:
            raise AppException(ErrorRegistry.ORG_NOT_FOUND)
        if org_id and parent_id == org_id:
            raise AppException(ErrorRegistry.CORE_INTEGRITY_ERROR)

    def create(self, data: OrganisationCreate) -> Organisation:
        if self.repo.get_by_nom(data.nom):
            raise AppException(ErrorRegistry.ORG_DUPLICATE, nom=data.nom)

        if data.parent_id:
            self._validate_parent(data.parent_id)

        org = Organisation(**data.model_dump())
        try:
            return self.repo.create(org)
        except IntegrityError as exc:
            raise AppException(ErrorRegistry.CORE_INTEGRITY_ERROR) from exc

    def update(self, identifiant: str, data: OrganisationUpdate) -> Organisation:
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        if "nom" in update_data and update_data["nom"] != obj.nom:
            if self.repo.get_by_nom(update_data["nom"]):
                raise AppException(ErrorRegistry.ORG_DUPLICATE, nom=update_data["nom"])

        if "parent_id" in update_data and update_data["parent_id"]:
            self._validate_parent(str(update_data["parent_id"]), identifiant)

        try:
            return self.repo.update(obj, update_data)
        except Exception as exc:
            raise AppException(ErrorRegistry.CORE_INTEGRITY_ERROR) from exc
