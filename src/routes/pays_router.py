from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker
from models import PaysCreate, PaysRead
from models.base_pagination import PaginatedResponse
from models.pays_model import PaysUpdate
from services.pays_service import PaysService

router = APIRouter(prefix="/pays", tags=["Pays"])
admin_only = RoleChecker(["ADMIN"])


def get_pays_service(db: Session = Depends(Database.get_session)) -> PaysService:
    return PaysService(db)


@router.post("/", response_model=PaysRead, status_code=status.HTTP_201_CREATED)
def create_pays(
    data: PaysCreate, db=Depends(Database.get_session), _=Depends(admin_only)
):
    return PaysService(db).create(data)


@router.get("/all", response_model=list[PaysRead])
def all_pays(db=Depends(Database.get_session)):
    return PaysService(db).repo.list_all()


@router.get("/", response_model=PaginatedResponse[PaysRead])
def list_pays(
    limit: int = 10, offset: int = 0, service: PaysService = Depends(get_pays_service)
):
    """
    Récupère la liste paginée des pays.
    """
    return service.list_paginated(limit=limit, offset=offset)


@router.get("/{id_pays}", response_model=PaysRead)
def get_pays(id_pays: str, service: PaysService = Depends(get_pays_service)):
    """Récupère un pays par son ID avec son organisation"""
    return service.get_one(id_pays)


@router.patch("/{id_pays}", response_model=PaysRead)
def update_pays(
    id_pays: str,
    data: PaysUpdate,
    service: PaysService = Depends(get_pays_service),
    _=Depends(admin_only),
):
    """Mise à jour partielle d'un pays (nom, code ou organisation)"""
    return service.update(id_pays, data)


@router.delete("/{id_pays}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pays(
    id_pays: str,
    service: PaysService = Depends(get_pays_service),
    _=Depends(admin_only),
):
    """Suppression d'un pays"""
    service.delete(id_pays)
