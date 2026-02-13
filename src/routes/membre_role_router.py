from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from conf.db.database import Database
from models import MembreRoleCreate, MembreRoleRead, MembreRoleUpdate
from services.membre_role_service import MembreRoleService

router = APIRouter(prefix="/membres-roles", tags=["Affectations Membres-Rôles"])


def get_service(db: Session = Depends(Database.get_session)):
    return MembreRoleService(db)


@router.post("/", response_model=MembreRoleRead, status_code=status.HTTP_201_CREATED)
def create_affectation(
    data: MembreRoleCreate, service: MembreRoleService = Depends(get_service)
):
    return service.create(data)


@router.patch("/{membre_id}/{role_code}", response_model=MembreRoleRead)
def update_affectation(
    membre_id: str,
    role_code: str,
    data: MembreRoleUpdate,
    service: MembreRoleService = Depends(get_service),
):
    return service.update_composite(membre_id, role_code, data)


@router.delete("/{membre_id}/{role_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_affectation(
    membre_id: str, role_code: str, service: MembreRoleService = Depends(get_service)
):
    # Formatage interne pour le repository
    service.delete(f"{membre_id}:{role_code}")
