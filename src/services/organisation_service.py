from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from core.exceptions import BadRequestException
from models import OrganisationICC, OrganisationICCCreate
from models.organisationicc_model import OrganisationICCRead, OrganisationICCUpdate
from repositories.organisation_repository import OrganisationRepository

from .base_service import BaseService


class OrganisationService(
    BaseService[
        OrganisationICCCreate,
        OrganisationICCRead,
        OrganisationICCUpdate,
        OrganisationICC,
    ]
):
    def __init__(self, db: Session):
        # On initialise la base avec le repo et le nom de la ressource pour
        # les messages d'erreur
        super().__init__(repo=OrganisationRepository(db), resource_name="Organisation")

    def create(self, data: OrganisationICCCreate) -> OrganisationICC:
        # Logique spécifique : vérification du nom unique
        if self.repo.get_by_nom(data.nom):
            raise BadRequestException(f"L'organisation '{data.nom}' existe déjà.")

        org = OrganisationICC(**data.model_dump())
        try:
            return self.repo.create(org)
        except IntegrityError as exc:
            raise BadRequestException(
                "Erreur d'intégrité lors de la création."
            ) from exc

    def update(self, identifiant: str, data: OrganisationICCUpdate) -> OrganisationICC:
        # On utilise get_one de la classe parente
        obj = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # Logique spécifique : vérification du nom si modifié
        if "nom" in update_data and update_data["nom"] != obj.nom:
            if self.repo.get_by_nom(update_data["nom"]):
                raise BadRequestException(
                    f"Le nom '{update_data['nom']}' est déjà utilisé."
                )

        try:
            return self.repo.update(obj, update_data)
        except Exception as exc:
            raise BadRequestException(
                f"Erreur lors de la mise à jour : {str(exc)}"
            ) from exc
