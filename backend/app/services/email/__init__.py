from app.core.config import settings
from app.services.email.base import EmailSender, EmailSendError
from app.services.email.smtp_sender import SmtpEmailSender


class _UnconfiguredEmailSender:
    # Fails loudly rather than pretending to send: the invite is saved and shows
    # "failed", so a missing .env entry is visible instead of silently losing mail.
    def send(self, to: str, subject: str, text_body: str) -> None:
        raise EmailSendError("Email is not configured on the server (SMTP settings missing).")


def get_email_sender() -> EmailSender:
    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password):
        return _UnconfiguredEmailSender()

    return SmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        user=settings.smtp_user,
        password=settings.smtp_password,
        from_address=settings.smtp_from_address or settings.smtp_user,
        timeout=settings.smtp_timeout_seconds,
    )
