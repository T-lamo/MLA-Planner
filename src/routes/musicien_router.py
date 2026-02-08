from models.musicien_model import MusicienCreate, MusicienRead, MusicienUpdate
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.musicien_service import MusicienService

from .base_route_factory import CRUDRouterFactory

factory = CRUDRouterFactory(
    service_class=MusicienService,
    create_schema=MusicienCreate,
    read_schema=MusicienRead,
    update_schema=MusicienUpdate,
    path="/musiciens",
    tag="Musiciens",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)

router = factory.router
