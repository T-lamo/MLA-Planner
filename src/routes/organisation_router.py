from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import RoleChecker
from models import OrganisationICCCreate, OrganisationICCRead
from models.base_pagination import PaginatedResponse
from models.organisationicc_model import OrganisationICCUpdate
from services.organisation_service import OrganisationService

router = APIRouter(prefix="/organisations", tags=["Organisations"])
admin_only = RoleChecker(["ADMIN"])


# ---------------------------
# Dépendance pour le service
# ---------------------------
def get_organisation_service(
    db: Session = Depends(Database.get_session),
) -> OrganisationService:
    return OrganisationService(db)


@router.get("/", response_model=PaginatedResponse[OrganisationICCRead])
def list_organisations(
    limit: int = 10,
    offset: int = 0,
    service: OrganisationService = Depends(get_organisation_service),
):
    """
    Récupère la liste des organisations avec pagination.
    """
    return service.list_paginated(limit=limit, offset=offset)


@router.get("/{id}", response_model=OrganisationICCRead)
def get_organisation(org_id: str, service=Depends(get_organisation_service)):
    return service.get_one(org_id)


@router.post(
    "/", response_model=OrganisationICCRead, status_code=status.HTTP_201_CREATED
)
def create_organisation(
    data: OrganisationICCCreate,
    service=Depends(get_organisation_service),
    _=Depends(admin_only),
):
    return service.create(data)


@router.patch("/{id}", response_model=OrganisationICCRead)
def update_organisation(
    org_id: str,
    data: OrganisationICCUpdate,
    service=Depends(get_organisation_service),
    _=Depends(admin_only),
):
    """Mise à jour partielle d'une organisation"""
    return service.update(org_id, data)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organisation(
    org_id: str, service=Depends(get_organisation_service), _=Depends(admin_only)
):
    """Suppression définitive d'une organisation"""
    service.delete(org_id)
