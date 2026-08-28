class AppError(Exception):
    """Base for typed domain exceptions. Services raise these; routers never build an
    HTTPException by hand. One handler (see app/main.py) translates status_code -> HTTP."""

    status_code: int = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AppError):
    """Google ID token failed verification: expired, bad signature, wrong audience,
    or wrong issuer."""

    status_code = 401
