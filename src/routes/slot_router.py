# src/routes/planning_routes.py

from models import SlotCreate, SlotRead, SlotUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.slot_service import SlotService

from .base_route_factory import CRUDRouterFactory

# 1. Routes pour SLOTS
factory = CRUDRouterFactory(
    service_class=SlotService,
    create_schema=SlotCreate,
    read_schema=SlotRead,
    update_schema=SlotUpdate,  # À affiner selon tes besoins Update
    path="/slots",
    tag="Slots",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router  # Expose le router pour l'inclure dans l'application FastAPI
