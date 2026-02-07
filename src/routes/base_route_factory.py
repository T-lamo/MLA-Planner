from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, SQLModel

from conf.db.database import Database
from models.base_pagination import PaginatedResponse

# Types génériques
C = TypeVar("C", bound=SQLModel)  # Create
U = TypeVar("U", bound=SQLModel)  # Update
R = TypeVar("R", bound=SQLModel)  # Read


class CRUDRouterFactory:
    """Usine générique pour générer des routes CRUD FastAPI."""

    def __init__(
        self,
        *,  # Force l'utilisation de mots-clés pour éviter R0917
        service_class: Type[Any],
        create_schema: Type[C],
        read_schema: Type[R],
        update_schema: Type[U],
        path: str,
        tag: str,
        dependencies: Optional[Dict[str, List[Any]]] = None,
    ):
        self.router = APIRouter(prefix=path, tags=[tag])
        self.service_class = service_class
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.deps = dependencies or {}

        self._setup_routes()

    def _setup_routes(self):
        # pylint: disable=too-many-locals
        # On utilise des alias snake_case pour satisfaire Pylint
        svc_cls = self.service_class
        schema_c = self.create_schema
        schema_r = self.read_schema
        schema_u = self.update_schema

        def get_service(db: Session = Depends(Database.get_session)):
            return svc_cls(db)

        @self.router.get(
            "/",
            response_model=PaginatedResponse[schema_r],  # type: ignore
            dependencies=self.deps.get("read", []),
        )
        def list_paginated(
            limit: int = 10, offset: int = 0, service=Depends(get_service)
        ):
            return service.list_paginated(limit=limit, offset=offset)

        @self.router.get("/all", response_model=List[schema_r])  # type: ignore
        def list_all(service=Depends(get_service)):
            print("list all")
            return service.repo.list_all()

        @self.router.get("/{item_id}", response_model=schema_r)  # type: ignore
        def get_one(item_id: str, service=Depends(get_service)):
            return service.get_one(item_id)

        @self.router.post(
            "/",
            response_model=schema_r,  # type: ignore
            status_code=status.HTTP_201_CREATED,
            dependencies=self.deps.get("create", []),
        )
        def create(data: schema_c, service=Depends(get_service)):  # type: ignore
            return service.create(data)

        @self.router.patch(
            "/{item_id}",
            response_model=schema_r,  # type: ignore
            dependencies=self.deps.get("update", []),
        )
        def update(
            item_id: str, data: schema_u, service=Depends(get_service)  # type: ignore
        ):
            return service.update(item_id, data)

        @self.router.delete(
            "/{item_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=self.deps.get("delete", []),
        )
        def delete(item_id: str, service=Depends(get_service)):
            service.delete(item_id)
