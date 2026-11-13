import smtplib
import ssl
from email.message import EmailMessage

from app.services.email.base import EmailSendError


class SmtpEmailSender:
    """The only file that imports smtplib — see docs/adr/0017."""

    def __init__(
        self, *, host: str, port: int, user: str, password: str, from_address: str, timeout: int
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_address = from_address
        self._timeout = timeout

    def send(self, to: str, subject: str, text_body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text_body)

        try:
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(self._user, self._password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            # Only the exception class name: SMTP error text can echo the message
            # envelope, and the body of this message contains the invite token.
            raise EmailSendError(f"Could not send email ({type(exc).__name__}).") from exc
