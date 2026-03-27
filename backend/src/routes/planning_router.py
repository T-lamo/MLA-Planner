from typing import Optional

from fastapi import BackgroundTasks, Depends, Query, status
from sqlmodel import Session

from conf.db.database import Database
from core.auth.auth_dependencies import (
    RoleChecker,
    get_active_campus,
    get_current_active_user,
)
from mla_enum.custom_enum import PlanningStatusCode
from models import (
    DataListResponse,
    DataResponse,
    PlanningServiceCreate,
    PlanningServiceRead,
    PlanningServiceUpdate,
    SlotCreate,
    SlotRead,
    Utilisateur,
)
from models.planning_model import (
    PlanningFullCreate,
    PlanningFullRead,
    PlanningFullUpdate,
)
from notification.notification_repository import EmailRepository
from notification.notification_service import EmailService
from routes.deps import STANDARD_ADMIN_ONLY_DEPS
from services.planing_service import PlanningServiceSvc
from services.slot_service import SlotService

from .base_route_factory import CRUDRouterFactory

# Dépendance partagée pour la gestion du planning (RESPONSABLE+ requis)
planning_manager = Depends(RoleChecker(["RESPONSABLE_MLA", "ADMIN", "Super Admin"]))

# Configuration du Router Factory pour Planning
factory = CRUDRouterFactory(
    service_class=PlanningServiceSvc,
    create_schema=PlanningServiceCreate,
    read_schema=PlanningServiceRead,
    update_schema=PlanningServiceUpdate,
    path="/plannings",
    tag="Plannings",
    dependencies=STANDARD_ADMIN_ONLY_DEPS,
)
router = factory.router


@router.post(
    "/{planning_id}/slots",
    response_model=DataResponse[SlotRead],
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un créneau à un planning existant",
    description=(
        "Crée un nouveau créneau lié à un planning spécifique. "
        "Vérifie la cohérence temporelle avec l'activité parente."
    ),
    dependencies=[planning_manager],
)
def create_slot_for_planning(
    planning_id: str,
    data: SlotCreate,
    db: Session = Depends(Database.get_db_for_route),
):
    """Point d'entrée pour l'ajout unitaire de créneaux."""
    svc = PlanningServiceSvc(db)
    svc.get_one(planning_id)
    slot_svc = SlotService(db)
    return {"data": slot_svc.add_slot_to_planning(planning_id, data)}


@router.post(
    "/slots",
    response_model=DataResponse[SlotRead],
    status_code=status.HTTP_201_CREATED,
    summary="Création directe de créneau",
    description="Permet de créer un créneau en spécifiant directement le planning_id.",
    dependencies=[planning_manager],
)
def add_slot(slot_data: SlotCreate, db: Session = Depends(Database.get_db_for_route)):
    service = PlanningServiceSvc(db)
    return {"data": service.create_slot(slot_data)}


@router.post(
    "/full",
    response_model=DataResponse[PlanningFullRead],
    status_code=status.HTTP_201_CREATED,
    summary="Création complète (Activité + Planning + Slots)",
    description=(
        "Point d'entrée atomique pour créer tout l'écosystème d'un planning. "
        "Valide les rôles des membres et l'absence de collisions."
    ),
    dependencies=[planning_manager],
)
def create_full_planning_endpoint(
    data: PlanningFullCreate,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    planning_db = svc.create_full_planning(data)
    return {"data": svc.get_full_planning(planning_db.id)}


@router.patch(
    "/{planning_id}/full",
    response_model=DataResponse[PlanningFullRead],
    status_code=status.HTTP_200_OK,
    summary="Mise à jour intégrale et synchronisation",
    description=(
        "Met à jour l'activité et le planning. Synchronise les slots : "
        "ajoute les nouveaux, met à jour les existants, supprime les absents."
    ),
    dependencies=[planning_manager],
)
def update_full_planning_endpoint(
    planning_id: str,
    data: PlanningFullUpdate,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    svc.update_full_planning(planning_id, data)
    return {"data": svc.get_full_planning(planning_id)}


@router.patch(
    "/{planning_id}/status",
    response_model=DataResponse[PlanningFullRead],
    summary="Changer le statut du workflow",
    description=(
        "Fait progresser le planning dans son cycle de vie "
        "(ex: de BROUILLON à PUBLIE ou ANNULE)."
    ),
    dependencies=[planning_manager],
)
def change_planning_status(
    planning_id: str,
    new_status: PlanningStatusCode,
    background_tasks: BackgroundTasks,
    db: Session = Depends(Database.get_db_for_route),
):
    svc = PlanningServiceSvc(db)
    email_svc = EmailService(EmailRepository())
    svc.update_planning_status(
        planning_id,
        new_status,
        background_tasks=background_tasks,
        email_service=email_svc,
    )
    return {"data": svc.get_full_planning(planning_id)}


@router.delete(
    "/{planning_id}/full",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Suppression totale (Cascade descendante)",
    description=(
        "Supprime le planning, ses slots, ses affectations et l'activité associée. "
        "Opération irréversible soumise à validation de statut."
    ),
    dependencies=[planning_manager],
)
def delete_full_planning_endpoint(
    planning_id: str, db: Session = Depends(Database.get_db_for_route)
):
    """Exécute la suppression complète via le service expert."""
    svc = PlanningServiceSvc(db)
    svc.delete_full_planning(planning_id)


@router.get("/{planning_id}/full", response_model=DataResponse[PlanningFullRead])
def read_full_planning(
    planning_id: str,
    db: Session = Depends(Database.get_db_for_route),
    _: Utilisateur = Depends(get_current_active_user),
):
    svc = PlanningServiceSvc(db)
    return {"data": svc.get_full_planning(planning_id)}


@router.get(
    "/my/calendar",
    response_model=DataListResponse[PlanningFullRead],
    summary="Plannings personnels de l'utilisateur connecté",
    description=(
        "Retourne tous les plannings complets où l'utilisateur connecté "
        "est affecté dans au moins un créneau."
    ),
)
def list_my_calendar(
    campus_id: str = Depends(get_active_campus),
    current_user: Utilisateur = Depends(get_current_active_user),
    db: Session = Depends(Database.get_db_for_route),
):
    if not current_user.membre_id:
        return {"data": []}
    svc = PlanningServiceSvc(db)
    return {"data": svc.list_my_plannings_full(current_user.membre_id, campus_id)}


@router.get(
    "/by-ministere/{ministere_id}",
    response_model=DataListResponse[PlanningFullRead],
    summary="Plannings d'un ministère",
    description=(
        "Retourne tous les plannings complets (activité + slots + affectations) "
        "organisés par un ministère donné. Accessible à tout utilisateur authentifié."
    ),
)
def list_by_ministere(
    ministere_id: str,
    campus_id: Optional[str] = Query(None),
    db: Session = Depends(Database.get_db_for_route),
    current_user: Utilisateur = Depends(get_current_active_user),
):
    svc = PlanningServiceSvc(db)
    return {"data": svc.list_by_ministere(ministere_id, current_user, campus_id)}


@router.get(
    "/by-campus/{campus_id}",
    response_model=DataListResponse[PlanningFullRead],
    summary="Plannings d'un campus",
    description=(
        "Retourne tous les plannings complets (activité + slots + affectations) "
        "dont l'activité se déroule sur le campus spécifié."
    ),
)
def list_by_campus(
    campus_id: str,
    db: Session = Depends(Database.get_db_for_route),
    current_user: Utilisateur = Depends(get_current_active_user),
):
    svc = PlanningServiceSvc(db)
    return {"data": svc.list_by_campus(campus_id, current_user)}


# Garantit que les routes littérales (ex: /by-ministere/..., /full, /slots)
# sont évaluées avant les routes paramétriques (ex: /{planning_id}).
router.routes.sort(key=lambda r: (1 if "{" in getattr(r, "path", "") else 0))
