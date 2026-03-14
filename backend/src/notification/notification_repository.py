from email.message import EmailMessage

import aiosmtplib

from .config import settings


class EmailRepository:
    """Gère l'envoi physique de l'email via SMTP (aiosmtplib async)."""

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
