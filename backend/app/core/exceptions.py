class AppError(Exception):
    """Base for typed domain exceptions. Services raise these; routers never build an
    HTTPException by hand. One handler (see app/main.py) translates status_code -> HTTP."""

    status_code: int = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AppError):
    """Google ID token failed verification: expired, bad signature, wrong audience,
    or wrong issuer. Also used for email/password login — same 401 whether the email
    is unknown or the password is wrong, so a response never tells an attacker which
    account exists."""

    status_code = 401


class EmailAlreadyExistsError(AppError):
    """Signup with an email that already has an account — Google-only or password,
    doesn't matter, this phase doesn't offer a "link accounts" flow for signup."""

    status_code = 409


class RateLimitedError(AppError):
    """Too many requests from one source in the current window — see
    core/rate_limit.py and docs/adr/0011-in-memory-rate-limiting.md."""

    status_code = 429


class EnrollmentAlreadyCompleteError(AppError):
    """A voiceprint already exists — submitting another sample would silently mix
    a fourth embedding into a centroid meant to average exactly three. The client
    must call DELETE /enrollment first."""

    status_code = 409


class EnrollmentAudioNotFoundError(AppError):
    """audio_key doesn't exist in R2 — the presigned PUT never completed, or the
    key was already consumed by a reset."""

    status_code = 404


class MLServiceUnavailableError(AppError):
    """The /ml embedding service didn't respond. An infra fault, not a judgment on
    the sample — does not count toward the three-strikes 'failed' status."""

    status_code = 503
