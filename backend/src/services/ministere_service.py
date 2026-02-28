import logging
from typing import List

from sqlmodel import Session, col, select

from core.exceptions import BadRequestException, NotFoundException
from models import Ministere, MinistereCreate, MinistereRead, MinistereUpdate
from models.schema_db_model import Campus  # Import du modèle de table
from repositories.campus_repository import CampusRepository
from repositories.ministere_repository import MinistereRepository
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class MinistereService(
    BaseService[MinistereCreate, MinistereRead, MinistereUpdate, Ministere]
):
    def __init__(self, db: Session):
        # On passe le repo à la classe parente
        super().__init__(repo=MinistereRepository(db), resource_name="Ministère")
        self.db = db
        self.campus_repo = CampusRepository(db)

    def create(self, data: MinistereCreate) -> Ministere:
        """
        Crée un ministère et l'associe à un ou plusieurs campus.
        """
        # 1. Vérification proactive du doublon de nom
        #  global (puisque unique=True sur le nom)
        statement = select(Ministere).where(Ministere.nom == data.nom)
        if self.db.exec(statement).first():
            raise BadRequestException(
                f"Le ministère '{data.nom}' existe déjà dans l'organisation."
            )

        # 2. Préparation de l'objet sans les relations
        # On exclut campus_ids du dump pour l'instanciation du modèle de table
        ministere_data = data.model_dump(exclude={"campus_ids"})
        db_obj = Ministere(**ministere_data)

        # 3. Synchronisation des campus (Many-to-Many)
        if data.campus_ids:
            self._sync_campuses(db_obj, data.campus_ids)
        else:
            # Optionnel : Règle métier - un ministère doit-il être
            #  lié à au moins un campus ?
            raise BadRequestException(
                "Un ministère doit être lié à au moins un campus."
            )

        return self._execute_with_flush(
            lambda: self.repo.create(db_obj),
            "Erreur d'intégrité : vérifiez les données du ministère.",
        )

    def update(self, identifiant: str, data: MinistereUpdate) -> Ministere:
        """
        Met à jour les informations du ministère et ses campus rattachés.
        """
        obj_db = self.get_one(identifiant)

        # Extraction des données scalaires
        update_data = data.model_dump(exclude_unset=True, exclude={"campus_ids"})

        # Mise à jour des relations Many-to-Many si fournies
        if data.campus_ids is not None:
            self._sync_campuses(obj_db, data.campus_ids)

        return self._execute_with_flush(
            lambda: self.repo.update(obj_db, update_data),
            "Mise à jour impossible : violation d'intégrité.",
        )

    def _sync_campuses(self, ministere: Ministere, campus_ids: List[str]) -> None:
        """
        Logique de synchronisation optimisée pour la relation N:N avec les campus.
        """
        if not campus_ids:
            ministere.campuses = []
            return

        # Récupération groupée pour éviter le N+1 (une seule requête pour tous les IDs)
        statement = select(Campus).where(col(Campus.id).in_(campus_ids))
        found_campuses = self.db.exec(statement).all()

        # Vérification si tous les IDs fournis existent en base
        if len(found_campuses) != len(set(campus_ids)):
            found_ids = {c.id for c in found_campuses}
            missing_ids = set(campus_ids) - found_ids
            raise NotFoundException(f"Campus suivants introuvables : {missing_ids}")

        # Mise à jour de la relation Many-to-Many
        ministere.campuses = list(found_campuses)
