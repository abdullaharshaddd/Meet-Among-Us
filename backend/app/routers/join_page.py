"""The page an emailed invite link opens. It only tells the person what to do in the app: the app is where joining
happens, so there is nothing to sign in to here. It shows what the invite preview already shows (workspace name
and who invited), plus the invite code to paste.
"""

import html

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import AppError
from app.services import invite_service

router = APIRouter(tags=["invites"])

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Join a workspace</title>
<style>body{{font-family:system-ui,sans-serif;max-width:32rem;margin:3rem auto;padding:0 1rem;line-height:1.5}}
code{{display:block;padding:.75rem;background:#eee;border-radius:.4rem;word-break:break-all}}</style></head>
<body>{body}</body></html>"""


@router.get("/join/{token}", response_class=HTMLResponse, include_in_schema=False)
def invite_landing_page(token: str, db: Session = Depends(get_db)) -> HTMLResponse:
    try:
        preview = invite_service.preview(db, token)
    except AppError as error:
        body = f"<h1>This invite can't be used</h1><p>{html.escape(error.message)}</p>"

        return HTMLResponse(PAGE.format(body=body), status_code=error.status_code)

    body = (
        f"<h1>Join {html.escape(preview.workspace_name)}</h1>"
        f"<p>{html.escape(preview.invited_by_name)} invited you. Open the Meet Among Us app, go to Workspaces, "
        'choose "Join a workspace" and paste this invite code:</p>'
        f"<code>{html.escape(token)}</code>"
        f"<p>The invite expires on {preview.expires_at:%Y-%m-%d}.</p>"
    )

    return HTMLResponse(PAGE.format(body=body))
