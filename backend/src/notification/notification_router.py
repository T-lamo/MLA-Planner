from fastapi import APIRouter, BackgroundTasks, Depends

from .notification_repository import EmailRepository
from .notification_schemas import PlanningNotification
from .notification_service import EmailService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Injection de dépendances
def get_email_service():
    repo = EmailRepository()
    return EmailService(repo)


@router.post("/send-planning")
async def send_planning_notification(
    notification: PlanningNotification,
    background_tasks: BackgroundTasks,
    service: EmailService = Depends(get_email_service),
):
    """
    Endpoint pour notifier un utilisateur.
    L'envoi est délégué aux BackgroundTasks pour une réponse instantanée.
    """
    background_tasks.add_task(service.notify_user_of_planning, notification)

    return {"status": "success", "message": "Email mis en file d'attente d'envoi."}
