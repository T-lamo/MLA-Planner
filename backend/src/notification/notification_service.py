import logging
import os
import urllib.parse
from datetime import datetime, timezone
from uuid import uuid4

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

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        """Convertit un datetime naïf (Europe/Paris) ou aware en UTC."""
        try:
            from zoneinfo import ZoneInfo  # pylint: disable=import-outside-toplevel

            tz_paris = ZoneInfo("Europe/Paris")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz_paris)
            return dt.astimezone(ZoneInfo("UTC"))
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            return dt.replace(tzinfo=timezone.utc)

    def _build_event_title(self, data: PlanningPublishedNotification) -> str:
        """Construit le titre de l'événement agenda."""
        date_str = data.date_activite.strftime("%d/%m/%Y")
        return f"{date_str} - {data.type_activite} - {data.role_code}"

    def _build_google_calendar_url(self, data: PlanningPublishedNotification) -> str:
        """Génère l'URL Google Calendar (ajout en 1 clic, sans OAuth)."""
        dt_start = self._to_utc(data.date_debut_dt)
        dt_end = self._to_utc(data.date_fin_dt)
        description = (
            f"Ministère : {data.ministere_nom}\n"
            f"Créneau : {data.nom_creneau}\n"
            f"Campus : {data.campus_nom}"
        )
        params = {
            "action": "TEMPLATE",
            "text": self._build_event_title(data),
            "dates": (
                f"{dt_start.strftime('%Y%m%dT%H%M%SZ')}/"
                f"{dt_end.strftime('%Y%m%dT%H%M%SZ')}"
            ),
            "details": description,
            "location": data.lieu or "",
        }
        base = "https://calendar.google.com/calendar/render"
        return f"{base}?{urllib.parse.urlencode(params)}"

    def _build_ics_content(self, data: PlanningPublishedNotification) -> bytes:
        """Génère le contenu ICS (RFC 5545) sans dépendance externe."""
        dt_start = self._to_utc(data.date_debut_dt)
        dt_end = self._to_utc(data.date_fin_dt)
        dtstamp = datetime.now(tz=timezone.utc)
        uid = f"{uuid4()}@mla-planning"
        description = (
            f"Ministère : {data.ministere_nom}\\n"
            f"Créneau : {data.nom_creneau}\\n"
            f"Campus : {data.campus_nom}"
        )
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//MLA Planning//FR",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{self._build_event_title(data)}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{data.lieu or ''}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "\r\n".join(lines).encode("utf-8")

    async def notify_planning_published(
        self, data: PlanningPublishedNotification
    ) -> None:
        """Notifie un membre affecté que son planning a été publié."""
        try:
            template = self.jinja_env.get_template("planning_published.html")
            date_str = data.date_activite.strftime("%A %d %B %Y").capitalize()
            google_url = self._build_google_calendar_url(data)
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
                google_calendar_url=google_url,
            )
            ics_bytes = self._build_ics_content(data)
            ics_filename = f"planning_{data.date_activite.strftime('%Y%m%d')}.ics"
            subject = f"✅ Planning publié – {data.type_activite}" f" du {date_str}"
            await self.repository.send_html_email_with_ics(
                subject=subject,
                recipient=str(data.email),
                html_content=html_content,
                ics_bytes=ics_bytes,
                ics_filename=ics_filename,
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
