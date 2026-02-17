from core.exceptions import ConflictException, NotFoundException
from models import Equipe, EquipeCreate, EquipeMembre, EquipeRead, EquipeUpdate, Membre
from repositories.equipe_repository import EquipeRepository
from services.base_service import BaseService
from sqlmodel import Session


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
            raise NotFoundException(f"Membre {membre_id} introuvable.")

        # 2. Vérifier si déjà présent
        existing = self.db.get(EquipeMembre, (equipe_id, membre_id))
        if existing:
            raise ConflictException("Ce membre est déjà dans cette équipe.")

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
            raise NotFoundException("Le membre ne fait pas partie de cette équipe.")

        self.db.delete(lien)
        self.db.flush()
