"""Summarizes a transcript. The model cites transcript turns by number; this service turns
each number back into a start time and a speaker so a person can check the claim. See
docs/adr/0026-grounding-with-turn-citations.md.
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import ml_client
from app.core.config import settings
from app.core.exceptions import NothingToSummarizeError, SummaryTooLongError
from app.models.user import User
from app.schemas.summary import (
    Citation,
    SummarizeRequest,
    SummarizeResponse,
    SummaryActionItem,
    SummaryDecision,
    SummarySentence,
    SummaryTurn,
)
from app.schemas.transcript import TranscribeResponse, TranscriptEntry
from app.services import permissions, speaker_id_service, transcript_service


def summarize(db: Session, user: User, workspace_id: UUID, request: SummarizeRequest) -> SummarizeResponse:
    transcript = None

    if request.audio_key is not None:
        # transcribe() checks membership and that the clip belongs to this workspace.
        transcript = transcript_service.transcribe(
            db,
            user,
            workspace_id,
            request.audio_key,
            request.transcription_engine,
            request.transcription_language,
            request.participant_user_ids,
        )
        entries = transcript.entries
    else:
        permissions.require_member(db, workspace_id, user.id)
        # Matching already happened for these entries, so the list changes nothing here. It is still
        # checked, so a bad id fails the same way on every endpoint instead of being ignored.
        speaker_id_service.require_participants(db, workspace_id, request.participant_user_ids)
        entries = request.entries

    if not entries:
        raise NothingToSummarizeError("The transcript has no speech to summarize.")

    # Numbered from 1: the model is told to cite these numbers and nothing else.
    turns = [
        {"index": number, "speaker": entry.speaker_label, "start": entry.start, "text": entry.text}
        for number, entry in enumerate(entries, start=1)
    ]
    result = summarize_turns(turns, request.summary_engine)

    return build_response(result, entries, transcript)


def build_response(
    result: ml_client.MLSummary,
    entries: list[SummaryTurn] | list[TranscriptEntry],
    transcript: TranscribeResponse | None,
) -> SummarizeResponse:
    def citations(turn_numbers: list[int]) -> list[Citation]:
        return [
            Citation(
                turn_number=number,
                start=entries[number - 1].start,
                speaker_label=entries[number - 1].speaker_label,
            )
            for number in sorted(set(turn_numbers))
        ]

    return SummarizeResponse(
        engine=result.engine,
        model=result.model,
        attempts=result.attempts,
        parts=result.parts,
        dropped_decisions=result.dropped_decisions,
        dropped_action_items=result.dropped_action_items,
        transcript=transcript,
        summary=[SummarySentence(text=p.text, citations=citations(p.turns), warnings=p.warnings) for p in result.summary],
        key_points=[
            SummarySentence(text=p.text, citations=citations(p.turns), warnings=p.warnings) for p in result.key_points
        ],
        decisions=[
            SummaryDecision(
                decision=d.decision,
                decided_by=d.decided_by,
                quote=d.quote,
                citations=citations(d.turns),
                warnings=d.warnings,
            )
            for d in result.decisions
        ],
        action_items=[
            SummaryActionItem(
                task=a.task,
                owner=a.owner,
                deadline=a.deadline,
                quote=a.quote,
                citations=citations(a.turns),
                warnings=a.warnings,
            )
            for a in result.action_items
        ],
    )


def summarize_turns(turns: list[dict], engine: str | None) -> ml_client.MLSummary:
    """Summarizes any length of transcript. Short ones go in one request. Long ones are cut into parts at
    turn boundaries, each part is summarized with the same turn numbers (so every citation still points at
    the right turn), and the parts are merged. See docs/adr/0029-split-then-merge-summaries.md."""
    results: list[ml_client.MLSummary] = []

    for part in split_into_parts(turns, settings.summary_part_max_chars):
        results += _summarize_part(part, engine)

    return merge_summaries(results)


def split_into_parts(turns: list[dict], max_chars: int) -> list[list[dict]]:
    parts: list[list[dict]] = [[]]
    size = 0

    for turn in turns:
        turn_size = len(turn["text"]) + len(turn["speaker"]) + 20  # 20 for the number and time in front

        if parts[-1] and size + turn_size > max_chars:
            parts.append([])
            size = 0

        parts[-1].append(turn)
        size += turn_size

    return parts


def _summarize_part(part: list[dict], engine: str | None) -> list[ml_client.MLSummary]:
    try:
        return [ml_client.summarize(part, engine)]
    except SummaryTooLongError:
        # The size estimate was too generous for this provider. Halve the part and try each half.
        if len(part) == 1:
            raise

        middle = len(part) // 2

        return _summarize_part(part[:middle], engine) + _summarize_part(part[middle:], engine)


def _same_text(text: str) -> str:
    return " ".join(re.sub(r"[\W_]+", " ", text.casefold()).split())


def merge_summaries(results: list[ml_client.MLSummary]) -> ml_client.MLSummary:
    """Puts the parts back together in order. Summary sentences simply follow each other, and an item that
    two parts both report (same words) is kept once."""
    if len(results) == 1:
        return results[0]

    def keep_first(items: list, text_of) -> list:
        seen: set[str] = set()
        kept = []

        for item in items:
            key = _same_text(text_of(item))

            if key not in seen:
                seen.add(key)
                kept.append(item)

        return kept

    def all_of(name: str) -> list:
        return [item for result in results for item in getattr(result, name)]

    return ml_client.MLSummary(
        engine=results[0].engine,
        model=results[0].model,
        attempts=max(result.attempts for result in results),
        dropped_decisions=sum(result.dropped_decisions for result in results),
        dropped_action_items=sum(result.dropped_action_items for result in results),
        parts=len(results),
        summary=all_of("summary"),
        key_points=keep_first(all_of("key_points"), lambda point: point.text),
        decisions=keep_first(all_of("decisions"), lambda decision: decision.decision),
        action_items=keep_first(all_of("action_items"), lambda action: action.task),
    )
