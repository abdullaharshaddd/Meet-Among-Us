"""Dev-only browser page for trying transcription: pick a workspace, record or upload a clip,
choose an engine (or both side by side) and read the transcript by speaker.

app/main.py only imports and mounts this router when DEV_TOOLS_ENABLED=true, the same rule as
the enrollment harness (docs/adr/0015-dev-enrollment-harness.md). The page uses the real
endpoints (/auth/login, /workspaces, /workspaces/{id}/uploads, /workspaces/{id}/transcribe), so
this module serves HTML and one dev-only member list for the participant picker (the real
members endpoint lives on the unmerged invites branch).
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.speaker_id import ParticipantChoice
from app.services import speaker_id_service

router = APIRouter(prefix="/dev/transcribe", tags=["dev"])

_HTML_PATH = Path(__file__).resolve().parent.parent / "dev_static" / "transcribe.html"


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def transcribe_harness_page() -> HTMLResponse:
    # Read per request so editing the page and refreshing needs no restart.
    return HTMLResponse(_HTML_PATH.read_text(encoding="utf-8"))


@router.get("/members", response_model=list[ParticipantChoice], include_in_schema=False)
def workspace_members(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ParticipantChoice]:
    return speaker_id_service.list_participant_choices(db, user, workspace_id)
