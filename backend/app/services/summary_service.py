"""Summarizes a transcript. The model cites transcript turns by number; this service turns
each number back into a start time and a speaker so a person can check the claim. See
docs/adr/0026-grounding-with-turn-citations.md.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core import ml_client
from app.core.exceptions import NothingToSummarizeError
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
from app.services import permissions, transcript_service


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
        entries = request.entries

    if not entries:
        raise NothingToSummarizeError("The transcript has no speech to summarize.")

    # Numbered from 1: the model is told to cite these numbers and nothing else.
    turns = [
        {"index": number, "speaker": entry.speaker_label, "start": entry.start, "text": entry.text}
        for number, entry in enumerate(entries, start=1)
    ]
    result = ml_client.summarize(turns, request.summary_engine)

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
