from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from .config import settings


class EmailRepository:
    """Gère l'envoi physique de l'email via SMTP (aiosmtplib async)."""

    @staticmethod
    def _build_mixed_message(
        subject: str,
        from_addr: str,
        recipient: str,
        html_content: str,
        *,
        ics_bytes: bytes,
        ics_filename: str,
    ) -> MIMEMultipart:
        """Construit un message multipart/mixed (HTML + pièce jointe .ics)."""
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = recipient
        alt = MIMEMultipart("alternative")
        alt.attach(
            MIMEText(
                "Veuillez utiliser un client email compatible HTML.",
                "plain",
                "utf-8",
            )
        )
        alt.attach(MIMEText(html_content, "html", "utf-8"))
        msg.attach(alt)
        ics_part = MIMEBase("text", "calendar", method="PUBLISH")
        ics_part.set_payload(ics_bytes)
        ics_part.add_header("Content-Disposition", "attachment", filename=ics_filename)
        msg.attach(ics_part)
        return msg

    async def send_html_email(
        self, subject: str, recipient: str, html_content: str
    ) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = recipient
        msg.set_content("Veuillez utiliser un client email compatible HTML.")
        msg.add_alternative(html_content, subtype="html")

        use_tls = settings.SMTP_PORT == 465
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=use_tls,
            start_tls=not use_tls,
        ) as server:
            await server.login(settings.SMTP_USER, settings.SMTP_PASS)
            await server.send_message(msg)

    async def send_html_email_with_ics(
        self,
        subject: str,
        recipient: str,
        html_content: str,
        *,
        ics_bytes: bytes,
        ics_filename: str,
    ) -> None:
        """Envoie un email HTML avec un fichier .ics en pièce jointe."""
        msg = self._build_mixed_message(
            subject,
            settings.EMAIL_FROM,
            recipient,
            html_content,
            ics_bytes=ics_bytes,
            ics_filename=ics_filename,
        )
        use_tls = settings.SMTP_PORT == 465
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=use_tls,
            start_tls=not use_tls,
        ) as server:
            await server.login(settings.SMTP_USER, settings.SMTP_PASS)
            await server.send_message(msg)
