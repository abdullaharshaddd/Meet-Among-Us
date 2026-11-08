"""The enrollment passages and the speech minimum, read from one JSON file.

backend/app/content/enrollment_passages.json is the only copy of this text. The dev
harness reads it through GET /enrollment/passages, the mobile app gets a generated copy
(npm run generate:passages), and docs/ENROLLMENT_PASSAGES.md is rendered from it by
scripts/render_passages_doc.py.
"""

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.enrollment import PassageContent, PassagesResponse

_CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "enrollment_passages.json"


@lru_cache(maxsize=1)
def load_passages() -> PassagesResponse:
    raw = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))

    return PassagesResponse(
        min_speech_seconds=raw["min_speech_seconds"],
        passages=[PassageContent(**passage) for passage in raw["passages"]],
    )


def min_speech_seconds() -> float:
    return load_passages().min_speech_seconds
