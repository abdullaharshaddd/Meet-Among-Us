"""Dev-only browser harness for voice enrollment — see
docs/adr/0015-dev-enrollment-harness.md.

Lets anyone on the same LAN enroll from a phone/laptop browser without an EAS
build, and surfaces the embedding math (centroid norm, variance, similarities)
the real API never returns. app/main.py only imports this module — and only
mounts `router` — when DEV_TOOLS_ENABLED=true, so a production deployment that
never sets that flag has no route here to hit at all.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import dev_enroll_service

router = APIRouter(prefix="/dev/enroll", tags=["dev"])

_HTML_PATH = Path(__file__).resolve().parent.parent / "dev_static" / "enroll.html"


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def enroll_harness_page() -> HTMLResponse:
    # Read from disk per request, not cached at import time — editing the
    # harness during a session and refreshing the browser should pick it up
    # without an uvicorn restart.
    return HTMLResponse(_HTML_PATH.read_text(encoding="utf-8"))


class SampleMeasurement(BaseModel):
    language: str
    accepted: bool
    reason_code: str | None
    duration_sec: float
    speech_duration_sec: float
    snr_db: float


@router.get("/api/samples", response_model=list[SampleMeasurement])
def sample_measurements(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SampleMeasurement]:
    return [SampleMeasurement(**row) for row in dev_enroll_service.list_sample_measurements(db, user)]


class PerPassageSimilarity(BaseModel):
    language: str
    similarity_to_centroid: float


class DiagnosticsResponse(BaseModel):
    centroid_l2_norm: float
    intra_speaker_variance: float
    sample_count: int
    model_version: str
    per_passage_similarity: list[PerPassageSimilarity]
    cross_language_similarity_en_ur: float | None


@router.get("/api/diagnostics", response_model=DiagnosticsResponse)
def diagnostics(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DiagnosticsResponse:
    result = dev_enroll_service.get_diagnostics(db, user)
    if result is None:
        raise HTTPException(status_code=404, detail="No voiceprint yet — all three passages must be accepted first")
    return DiagnosticsResponse(**result)


class AdminUserRow(BaseModel):
    email: str
    display_name: str
    enrollment_status: str
    accepted_sample_count: int
    total_sample_count: int
    intra_speaker_variance: float | None
    centroid_l2_norm: float | None


@router.get("/api/admin/users", response_model=list[AdminUserRow])
def admin_users(db: Session = Depends(get_db)) -> list[AdminUserRow]:
    # No auth beyond the router being mounted at all — see the ADR. Acceptable
    # for a handful of trusted teammates enrolling over one wifi network; this
    # must never be reachable anywhere a stranger could reach it.
    return [AdminUserRow(**row) for row in dev_enroll_service.list_admin_users(db)]
