from typing import Any

from sqlmodel import Session

from core.exceptions.exceptions import BadRequestException
from models import Affectation, AffectationCreate, AffectationRead
from repositories.affectation_repository import AffectationRepository
from repositories.slot_repository import SlotRepository
from services.base_service import BaseService


class AffectationService(
    BaseService[AffectationCreate, AffectationRead, Any, Affectation]
):
    def __init__(self, db: Session):
        super().__init__(AffectationRepository(db), "Affectation")
        self.slot_repo = SlotRepository(db)

    def create_affectation(self, data: AffectationCreate) -> Affectation:
        # 1. Récupérer les dates du slot pour vérifier les conflits
        slot = self.slot_repo.get_by_id(data.slot_id)
        if not slot:
            raise BadRequestException("Slot introuvable.")

        # 2. Vérifier le chevauchement (Overlap)
        if self.repo.check_overlap(data.membre_id, slot.date_debut, slot.date_fin):
            raise BadRequestException(
                "Ce membre est déjà affecté à un autre créneau sur cette période."
            )

        # 3. Création (La FK composite dans le modèle gère la
        #  vérification Membre/Rôle via la DB)
        try:
            return self.repo.create(Affectation(**data.model_dump()))
        except Exception as exc:
            raise BadRequestException(
                "Vérifiez que le membre possède bien la compétence requise."
            ) from exc
