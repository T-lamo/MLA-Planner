import logging
import os

from jinja2 import Environment, FileSystemLoader

from .config import settings
from .notification_repository import EmailRepository
from .notification_schemas import (
    PlanningCancelledNotification,
    PlanningNotification,
    PlanningPublishedNotification,
)

logger = logging.getLogger(__name__)

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class EmailService:
    def __init__(self, repository: EmailRepository):
        self.repository = repository
        self.jinja_env = Environment(
            loader=FileSystemLoader(_CURRENT_DIR), autoescape=True
        )

    async def notify_user_of_planning(self, data: PlanningNotification) -> None:
        """Méthode legacy — conservée pour compatibilité avec le router existant."""
        template = self.jinja_env.get_template("planning_notification.html")
        html_content = template.render(
            username=data.username,
            date=data.shift_start.strftime("%d/%m/%Y"),
            start_time=data.shift_start.strftime("%H:%M"),
            end_time=data.shift_end.strftime("%H:%M"),
            location=data.location,
        )
        subject = f"📅 Nouveau planning : {data.shift_start.strftime('%d/%m/%Y')}"
        await self.repository.send_html_email(
            subject=subject, recipient=data.email, html_content=html_content
        )

    async def notify_planning_published(
        self, data: PlanningPublishedNotification
    ) -> None:
        """Notifie un membre affecté que son planning a été publié."""
        try:
            template = self.jinja_env.get_template("planning_published.html")
            date_str = data.date_activite.strftime("%A %d %B %Y").capitalize()
            html_content = template.render(
                prenom=data.prenom,
                nom=data.nom,
                type_activite=data.type_activite,
                date_activite=date_str,
                heure_debut=data.heure_debut,
                heure_fin=data.heure_fin,
                lieu=data.lieu,
                campus_nom=data.campus_nom,
                ministere_nom=data.ministere_nom,
                nom_creneau=data.nom_creneau,
                role_code=data.role_code,
                app_url=settings.APP_URL,
            )
            subject = f"✅ Planning publié – {data.type_activite}" f" du {date_str}"
            await self.repository.send_html_email(
                subject=subject,
                recipient=str(data.email),
                html_content=html_content,
            )
        except (
            Exception
        ) as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            logger.error(
                "Échec notification publication — %s %s <%s>: %s",
                data.prenom,
                data.nom,
                data.email,
                exc,
            )

    async def notify_planning_cancelled(
        self, data: PlanningCancelledNotification
    ) -> None:
        """Notifie un membre affecté que son planning a été annulé."""
        try:
            template = self.jinja_env.get_template("planning_cancelled.html")
            date_str = data.date_activite.strftime("%A %d %B %Y").capitalize()
            html_content = template.render(
                prenom=data.prenom,
                nom=data.nom,
                type_activite=data.type_activite,
                date_activite=date_str,
                campus_nom=data.campus_nom,
                ministere_nom=data.ministere_nom,
                motif=data.motif,
            )
            subject = f"❌ Planning annulé – {data.type_activite}" f" du {date_str}"
            await self.repository.send_html_email(
                subject=subject,
                recipient=str(data.email),
                html_content=html_content,
            )
        except (
            Exception
        ) as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            logger.error(
                "Échec notification annulation — %s %s <%s>: %s",
                data.prenom,
                data.nom,
                data.email,
                exc,
            )
