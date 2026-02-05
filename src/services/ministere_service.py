from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from core.exceptions import BadRequestException, NotFoundException
from models import Ministere, MinistereCreate, MinistereRead, MinistereUpdate
from repositories.campus_repository import CampusRepository
from repositories.ministere_repository import MinistereRepository
from services.base_service import BaseService


class MinistereService(
    BaseService[MinistereCreate, MinistereRead, MinistereUpdate, Ministere]
):
    def __init__(self, db: Session):
        # On passe le repo à la classe parente
        super().__init__(repo=MinistereRepository(db), resource_name="Ministère")
        # On stocke la session pour les vérifications spécifiques
        self.db = db
        self.campus_repo = CampusRepository(db)

    def create(self, data: MinistereCreate) -> Ministere:
        # 1. Vérification critique : le campus doit exister
        if not self.campus_repo.get_by_id(data.campus_id):
            raise NotFoundException(f"Campus parent {data.campus_id} introuvable.")

        # 2. Vérification proactive du doublon de nom
        # On vérifie si un ministère avec ce nom existe déjà sur CE campus
        # (C'est souvent la règle métier : unique par campus)
        statement = select(Ministere).where(
            Ministere.nom == data.nom, Ministere.campus_id == data.campus_id
        )
        existing_min = self.db.exec(statement).first()

        if existing_min:
            raise BadRequestException(
                f"Le ministère '{data.nom}' existe déjà sur ce campus."
            )

        db_obj = Ministere(**data.model_dump())
        try:
            return self.repo.create(db_obj)
        except IntegrityError as exc:
            # Sécurité au cas où une race condition surviendrait
            self.db.rollback()
            raise BadRequestException(
                "Erreur d'intégrité : ce ministère existe déjà."
            ) from exc

    def update(self, identifiant: str, data: MinistereUpdate) -> Ministere:
        obj_db = self.get_one(identifiant)
        update_data = data.model_dump(exclude_unset=True)
        return self.repo.update(obj_db, update_data)
