from core.exceptions import BadRequestException, NotFoundException
from models import Pays, PaysCreate
from models.pays_model import PaysRead, PaysUpdate
from repositories.organisation_repository import OrganisationRepository
from repositories.pays_repository import PaysRepository
from services.base_service import BaseService
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


class PaysService(BaseService[PaysCreate, PaysRead, PaysUpdate, Pays]):
    def __init__(self, db: Session):
        # On passe le PaysRepository au BaseService (accessible via self.repo)
        super().__init__(repo=PaysRepository(db), resource_name="Pays")
        # On garde l'Org Repo pour les validations spécifiques à ce service
        self.org_repo = OrganisationRepository(db)

    def create(self, data: PaysCreate) -> Pays:
        # Validation spécifique : L'organisation parente doit exister
        if not self.org_repo.get_by_id(data.organisation_id):
            raise NotFoundException(
                f"Organisation ID {data.organisation_id} introuvable."
            )

        pays = Pays(**data.model_dump())
        try:
            return self.repo.create(pays)
        except IntegrityError as exc:
            raise BadRequestException("Le pays ou son code existe déjà.") from exc

    def update(self, identifiant: str, data: PaysUpdate) -> Pays:
        # 1. Utilise get_one() de la classe parente (gère déjà le 404)
        pays_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        # 2. Validation spécifique : vérifier la nouvelle organisation si fournie
        if "organisation_id" in update_data:
            if not self.org_repo.get_by_id(update_data["organisation_id"]):
                raise NotFoundException("La nouvelle organisation est invalide.")

        try:
            return self.repo.update(pays_db, update_data)
        except Exception as exc:
            raise BadRequestException(
                "Erreur lors de la mise à jour (nom ou code peut-être déjà pris)."
            ) from exc
