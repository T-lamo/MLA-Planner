import logging
from typing import List, cast

from sqlmodel import Session, col, select

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Campus, CampusCreate, CampusRead, CampusUpdate
from models.schema_db_model import Ministere  # Import du modèle pour la liaison
from repositories.campus_repository import CampusRepository
from repositories.organisation_repository import OrganisationRepository
from services.base_service import BaseService
from services.ministere_service import MinistereService

logger = logging.getLogger(__name__)


class CampusService(BaseService[CampusCreate, CampusRead, CampusUpdate, Campus]):
    def __init__(self, db: Session):
        super().__init__(repo=CampusRepository(db), resource_name="Campus")
        self.db = db
        self.org_repo = OrganisationRepository(db)
        self.ministere_svc = MinistereService(self.db)

    def create(self, data: CampusCreate) -> Campus:
        """Crée un campus après validation de l'existence de l'organisation."""
        if not self.org_repo.get_by_id(data.organisation_id):
            raise AppException(ErrorRegistry.ORG_NOT_FOUND)

        db_obj = Campus(**data.model_dump())
        return self._execute_with_flush(lambda: self.repo.create(db_obj))

    def update(self, identifiant: str, data: CampusUpdate) -> Campus:
        """Met à jour un campus avec validation différentielle de l'organisation."""
        campus_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        if "organisation_id" in update_data and update_data["organisation_id"]:
            if not self.org_repo.get_by_id(str(update_data["organisation_id"])):
                raise AppException(ErrorRegistry.ORG_NOT_FOUND)

        return self._execute_with_flush(
            lambda: self.repo.update(campus_db, update_data)
        )

    def link_ministeres(self, campus_id: str, ministere_ids: List[str]) -> Campus:
        """
        Liaison Many-to-Many : Associe une liste de ministères à un campus.
        Cette méthode remplace les liaisons existantes par la nouvelle liste.
        """
        campus_db = self.get_one(campus_id)

        if not ministere_ids:
            campus_db.ministeres = []
        else:
            # Récupération optimisée via Clause IN pour Mypy
            statement = select(Ministere).where(col(Ministere.id).in_(ministere_ids))
            found_ministeres = self.db.exec(statement).all()

            # Validation de l'existence de tous les ministères demandés
            if len(found_ministeres) != len(set(ministere_ids)):
                found_ids = {m.id for m in found_ministeres}
                missing_ids = set(ministere_ids) - found_ids
                raise AppException(ErrorRegistry.MINST_NOT_FOUND, id=str(missing_ids))

            campus_db.ministeres = list(found_ministeres)

        try:
            self.db.add(campus_db)
            self.db.flush()
            return campus_db
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la liaison campus-ministères : {e}")
            raise AppException(ErrorRegistry.CAMP_LINK_ERROR) from e

    def add_single_ministere(self, campus_id: str, ministere_id: str) -> Campus:
        """Ajoute un seul ministère à la liste existante sans supprimer les autres."""
        campus_db = self.get_one(campus_id)

        # Vérification si déjà lié
        if any(m.id == ministere_id for m in campus_db.ministeres):
            return campus_db

        ministere = self.db.get(Ministere, ministere_id)
        if not ministere:
            raise AppException(ErrorRegistry.MINST_NOT_FOUND, id=ministere_id)

        campus_db.ministeres.append(ministere)
        self.db.add(campus_db)
        self.db.flush()
        return campus_db

    def get_details(self, campus_id: str) -> Campus:
        """
        Récupère la structure complète du campus pour le schéma CampusReadWithDetails.
        """
        campus_db = self.repo.get_with_details(campus_id)

        if not campus_db:
            raise AppException(ErrorRegistry.CORE_RESOURCE_NOT_FOUND, resource="Campus")

        return campus_db

    def get_detailed_ministeres_by_campus(self, campus_id: str) -> List[Ministere]:
        """
        Orchestre la récupération enrichie des ministères d'un campus.
        """
        campus_db = self.get_details(campus_id)

        ministeres_list = cast(List[Ministere], campus_db.ministeres or [])

        detailed_ministeres: List[Ministere] = [
            self.ministere_svc.get_detailed(str(m.id))
            for m in ministeres_list
            if m.id is not None
        ]

        return detailed_ministeres
