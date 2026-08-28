from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.health import HealthResponse

app = FastAPI(title="AI Meeting Intelligence Agent")


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
