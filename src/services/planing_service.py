from sqlmodel import Session

from models import (
    PlanningService,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
)
from repositories.planning_repository import PlanningRepository  # Lazy import
from services.base_service import BaseService


class PlanningServiceSvc(
    BaseService[
        PlanningServiceCreate,
        PlanningServiceRead,
        PlanningServiceUpdate,
        PlanningService,
    ]
):
    def __init__(self, db: Session):
        super().__init__(PlanningRepository(db), "Planning")

    def create(self, data: PlanningServiceCreate) -> PlanningService:
        # 1. Manual validation of Activity existence
        # activite = self.db.get(Activite, data.activite_id)
        # if not activite:
        #     raise BadRequestException(f"Activité {data.activite_id} introuvable.")
        #
        # 2. The BaseService.create will handle the rest
        return super().create(data)
