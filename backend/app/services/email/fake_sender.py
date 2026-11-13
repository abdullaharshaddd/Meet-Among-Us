from dataclasses import dataclass

from app.services.email.base import EmailSendError


@dataclass(frozen=True)
class SentEmail:
    to: str
    subject: str
    text_body: str


class FakeEmailSender:
    """In-memory sender for tests: records messages instead of sending, and can be told
    to fail so the 'invite survives an email failure' path can be exercised."""

    def __init__(self, *, fail_with: str | None = None) -> None:
        self.sent: list[SentEmail] = []
        self.fail_with = fail_with

    def send(self, to: str, subject: str, text_body: str) -> None:
        if self.fail_with is not None:
            raise EmailSendError(self.fail_with)
        self.sent.append(SentEmail(to=to, subject=subject, text_body=text_body))
