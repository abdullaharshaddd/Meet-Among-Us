from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import AppError
from app.routers.auth import router as auth_router
from app.routers.enrollment import router as enrollment_router
from app.schemas.health import HealthResponse

app = FastAPI(title="AI Meeting Intelligence Agent")

# Expo web runs on a different origin (localhost:8081) than the API
# (localhost:8001), so the browser blocks the request without this.
# allow_origins=["*"] is dev-only — tighten to the real mobile/web origin(s)
# before shipping.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(enrollment_router)

if settings.dev_tools_enabled:
    # /dev/enroll only exists on a developer's own machine — see
    # docs/adr/0015-dev-enrollment-harness.md. The import lives inside this
    # branch, not just the mount, so a prod deploy that leaves the flag unset
    # never defines these routes at all, rather than merely hiding them.
    from app.routers.dev_enroll import router as dev_enroll_router

    app.include_router(dev_enroll_router)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # Single translation point from typed domain exceptions to HTTP — see
    # CLAUDE.md's "Errors: raise typed domain exceptions, translate to HTTP in one
    # exception handler." Routers and services never build an HTTPException by hand.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    # A bare 200 proves uvicorn is up, not that the pooler connection works.
    # SELECT 1 is what actually exercises DATABASE_URL end to end.
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001 — surface any DB failure reason in the response
        db_status = f"error: {exc}"
    return HealthResponse(status="ok", db=db_status)
