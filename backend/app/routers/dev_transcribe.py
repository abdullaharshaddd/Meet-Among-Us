"""Dev-only browser page for trying transcription: pick a workspace, record or upload a clip,
choose an engine (or both side by side) and read the transcript by speaker.

app/main.py only imports and mounts this router when DEV_TOOLS_ENABLED=true, the same rule as
the enrollment harness (docs/adr/0015-dev-enrollment-harness.md). The page uses the real
endpoints (/auth/login, /workspaces, /workspaces/{id}/uploads, /workspaces/{id}/transcribe), so
this module serves HTML and nothing else.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dev/transcribe", tags=["dev"])

_HTML_PATH = Path(__file__).resolve().parent.parent / "dev_static" / "transcribe.html"


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def transcribe_harness_page() -> HTMLResponse:
    # Read per request so editing the page and refreshing needs no restart.
    return HTMLResponse(_HTML_PATH.read_text(encoding="utf-8"))
