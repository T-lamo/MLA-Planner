from sqlmodel import Session, select

from core.exceptions import BadRequestException, NotFoundException
from models import Membre, MembreCreate, MembreRead, MembreUpdate, Utilisateur
from repositories.membre_repository import MembreRepository
from repositories.ministere_repository import MinistereRepository
from repositories.pole_repository import PoleRepository
from services.base_service import BaseService


class MembreService(BaseService[MembreCreate, MembreRead, MembreUpdate, Membre]):
    def __init__(self, db: Session):
        super().__init__(repo=MembreRepository(db), resource_name="Membre")
        self.db = db
        self.min_repo = MinistereRepository(db)
        self.pole_repo = PoleRepository(db)

    def create(self, data: MembreCreate) -> Membre:
        # Validation UUID existence
        if data.ministere_id and not self.min_repo.get_by_id(data.ministere_id):
            raise NotFoundException(f"Ministère {data.ministere_id} introuvable.")
        if data.pole_id and not self.pole_repo.get_by_id(data.pole_id):
            raise NotFoundException(f"Pôle {data.pole_id} introuvable.")

        return self.repo.create(Membre(**data.model_dump()))

    def link_utilisateur(self, user_id: str, membre_id: str) -> Utilisateur:
        membre = self.get_one(membre_id)
        user = self.db.get(Utilisateur, user_id)

        if not user:
            raise NotFoundException("Utilisateur introuvable.")

        # 1. Vérifier si ce membre a déjà un compte
        if self.db.exec(
            select(Utilisateur).where(Utilisateur.membre_id == membre_id)
        ).first():
            raise BadRequestException("Ce membre est déjà lié à un compte utilisateur.")

        # 2. Vérifier si cet utilisateur est déjà lié à un autre membre
        if user.membre_id:
            raise BadRequestException("Cet utilisateur est déjà lié à un membre.")

        user.membre_id = membre.id
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _after_delete_hook(self, obj: Membre) -> None:
        # On casse le lien avec l'utilisateur (SET NULL)
        if obj.utilisateur:
            obj.utilisateur.membre_id = None
            self.db.add(obj.utilisateur)

        self.db.commit()
