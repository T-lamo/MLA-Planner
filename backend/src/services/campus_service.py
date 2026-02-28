import logging
from typing import List

from sqlmodel import Session, col, select

from core.exceptions import BadRequestException, NotFoundException
from models import Campus, CampusCreate, CampusRead, CampusUpdate
from models.schema_db_model import Ministere  # Import du modèle pour la liaison
from repositories.campus_repository import CampusRepository
from repositories.pays_repository import PaysRepository
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class CampusService(BaseService[CampusCreate, CampusRead, CampusUpdate, Campus]):
    def __init__(self, db: Session):
        super().__init__(repo=CampusRepository(db), resource_name="Campus")
        self.db = db
        self.pays_repo = PaysRepository(db)

    def create(self, data: CampusCreate) -> Campus:
        """Crée un campus après validation de l'existence du pays."""
        if not self.pays_repo.get_by_id(data.pays_id):
            raise NotFoundException(f"Pays avec l'ID {data.pays_id} introuvable.")

        db_obj = Campus(**data.model_dump())
        return self._execute_with_flush(
            lambda: self.repo.create(db_obj),
            "Un campus avec ce nom existe déjà dans ce secteur.",
        )

    def update(self, identifiant: str, data: CampusUpdate) -> Campus:
        """Met à jour un campus avec validation différentielle du pays."""
        campus_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)

        if "pays_id" in update_data and update_data["pays_id"]:
            if not self.pays_repo.get_by_id(str(update_data["pays_id"])):
                raise NotFoundException("Le nouveau pays spécifié est invalide.")

        return self._execute_with_flush(
            lambda: self.repo.update(campus_db, update_data),
            "Mise à jour impossible : violation d'intégrité.",
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
                raise NotFoundException(f"Ministères introuvables : {missing_ids}")

            campus_db.ministeres = list(found_ministeres)

        try:
            self.db.add(campus_db)
            self.db.flush()
            # On commit ici seulement si ce service est appelé hors d'un orchestrateur
            # Sinon, laissez le commit au niveau du routeur ou de l'orchestrateur
            return campus_db
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la liaison campus-ministères : {e}")
            raise BadRequestException(
                "Impossible de mettre à jour les liaisons ministères."
            ) from e

    def add_single_ministere(self, campus_id: str, ministere_id: str) -> Campus:
        """Ajoute un seul ministère à la liste existante sans supprimer les autres."""
        campus_db = self.get_one(campus_id)

        # Vérification si déjà lié
        if any(m.id == ministere_id for m in campus_db.ministeres):
            return campus_db

        ministere = self.db.get(Ministere, ministere_id)
        if not ministere:
            raise NotFoundException(f"Ministère {ministere_id} introuvable.")

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
            raise NotFoundException(
                f"{self.resource_name} avec l'ID {campus_id} introuvable."
            )

        return campus_db
