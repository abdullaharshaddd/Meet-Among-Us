from typing import Protocol


class EmailSendError(Exception):
    """Any failure to hand a message to the mail server. The message is stored on the
    invite as email_error and shown to the Team Lead, so it must never contain a token
    or a password."""


class EmailSender(Protocol):
    def send(self, to: str, subject: str, text_body: str) -> None:
        """Raise EmailSendError on failure; return normally on success."""
        ...
