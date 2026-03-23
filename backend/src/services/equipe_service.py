from sqlmodel import Session

from core.exceptions.app_exception import AppException
from core.message import ErrorRegistry
from models import Equipe, EquipeCreate, EquipeMembre, EquipeRead, EquipeUpdate, Membre
from repositories.equipe_repository import EquipeRepository
from services.base_service import BaseService


class EquipeService(BaseService[EquipeCreate, EquipeRead, EquipeUpdate, Equipe]):
    def __init__(self, db: Session):
        super().__init__(repo=EquipeRepository(db), resource_name="Equipe")
        self.db = db

    def add_member(self, equipe_id: str, membre_id: str) -> EquipeMembre:
        """Associe un membre à une équipe avec validation."""
        # 1. Vérifier existence
        equipe = self.get_one(equipe_id)
        membre = self.db.get(Membre, membre_id)
        if not membre:
            raise AppException(ErrorRegistry.MEMBRE_NOT_FOUND)

        # 2. Vérifier si déjà présent
        existing = self.db.get(EquipeMembre, (equipe_id, membre_id))
        if existing:
            raise AppException(ErrorRegistry.TEAM_MEMBER_DUPLICATE)

        # 3. Créer le lien
        lien = EquipeMembre(equipe_id=equipe.id, membre_id=membre.id)
        self.db.add(lien)
        self.db.flush()
        self.db.refresh(lien)
        return lien

    def remove_member(self, equipe_id: str, membre_id: str) -> None:
        """Retire un membre de l'équipe."""
        lien = self.db.get(EquipeMembre, (equipe_id, membre_id))
        if not lien:
            raise AppException(ErrorRegistry.TEAM_MEMBER_NOT_FOUND)

        self.db.delete(lien)
        self.db.flush()
