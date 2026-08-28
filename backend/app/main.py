from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import AppError
from app.routers.auth import router as auth_router
from app.schemas.health import HealthResponse

app = FastAPI(title="AI Meeting Intelligence Agent")
app.include_router(auth_router)


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
