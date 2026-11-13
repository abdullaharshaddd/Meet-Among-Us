"""Turns a meeting's uploaded audio into a saved transcript, summary, decisions and action items, in the background.

Two steps, each saved as soon as it succeeds:
  1. transcript: identify the speakers among the attendees, transcribe, save the segments;
  2. summary: summarize the saved segments, save the summary, decisions and action items.
If a step fails the meeting is marked failed with the step and a readable reason. What already succeeded stays,
and a retry only runs the steps that are still missing. See docs/adr/0030-background-processing.md.
"""

import logging
import re
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    MLServiceUnavailableError,
    SummaryRateLimitedError,
    TranscriptionRateLimitedError,
)
from app.models.meeting import FailedStep, Meeting, MeetingAttendee, MeetingStatus
from app.models.meeting_result import (
    ActionItem,
    Decision,
    SegmentLanguage,
    SpeakerKind,
    Summary,
    TranscriptSegment,
)
from app.models.user import User
from app.repositories import meeting_repository, meeting_result_repository
from app.schemas.transcript import TranscriptEntry
from app.services import meeting_view, summary_service, transcript_service

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AbstractContextManager[Session]]
UNKNOWN_LABEL = re.compile(r"unknown speaker (\d+)", re.IGNORECASE)
GENERIC_REASON = "Something went wrong while processing this meeting. Press retry, and tell us if it keeps happening."


class StepFailed(Exception):
    def __init__(self, step: FailedStep, reason: str) -> None:
        super().__init__(reason)
        self.step = step
        self.reason = reason


def _now() -> datetime:
    return datetime.now(timezone.utc)


def reason_for(error: AppError) -> str:
    """A sentence a person can act on. The AppError messages never contain keys or stack traces."""
    if isinstance(error, MLServiceUnavailableError):
        return "The speech service could not be reached. Check that it is running, then press retry."

    if isinstance(error, (TranscriptionRateLimitedError, SummaryRateLimitedError)):
        return "The outside service is busy right now. Wait a minute, then press retry."

    return str(error)


def run(session_factory: SessionFactory, meeting_id: UUID) -> None:
    """What the background task calls. It opens its own session, because the request's session is gone by then."""
    try:
        with session_factory() as db:
            process(db, meeting_id)
    except Exception:
        logger.exception("Processing meeting %s crashed outside a step", meeting_id)


def process(db: Session, meeting_id: UUID) -> None:
    meeting = meeting_repository.get(db, meeting_id)

    if meeting is None or meeting.status != MeetingStatus.PROCESSING:
        return

    try:
        if meeting.transcribed_at is None:
            _transcript_step(db, meeting_id)

        if meeting_repository.get(db, meeting_id).summarized_at is None:
            _summary_step(db, meeting_id)
    except StepFailed as failure:
        db.rollback()
        meeting = meeting_repository.get(db, meeting_id)
        meeting.status = MeetingStatus.FAILED
        meeting.failed_step = failure.step
        meeting.failure_reason = failure.reason
        db.commit()

        return

    meeting = meeting_repository.get(db, meeting_id)
    meeting.status = MeetingStatus.DONE
    meeting.failed_step = None
    meeting.failure_reason = None
    db.commit()


def _guard(step: FailedStep, work: Callable[[], object]) -> object:
    """Runs one piece of work, and turns any failure into a StepFailed with a readable reason."""
    try:
        return work()
    except StepFailed:
        raise
    except AppError as error:
        raise StepFailed(step, reason_for(error)) from error
    except Exception as error:
        logger.exception("Unexpected failure in the %s step", step.value)

        raise StepFailed(step, GENERIC_REASON) from error


# --- step 1: transcript ----------------------------------------------------------------------------


def _transcript_step(db: Session, meeting_id: UUID) -> None:
    meeting = meeting_repository.get(db, meeting_id)
    audio = meeting_repository.get_audio(db, meeting_id)

    if audio is None or audio.uploaded_at is None:
        raise StepFailed(FailedStep.TRANSCRIPT, "No audio was uploaded for this meeting.")

    workspace_id = meeting.workspace_id
    audio_key = audio.audio_key
    # Only attendees can be matched. An empty set means nobody can be named, which is different from None.
    attendee_ids = {attendee.user_id for attendee, _ in meeting_repository.list_attendees(db, meeting_id) if attendee.user_id}

    # End the transaction before the slow calls, so the connection is not held open for minutes.
    db.commit()

    def work() -> tuple[float, list[TranscriptEntry]]:
        audio_bytes = storage.get_object_bytes(audio_key)
        duration = ml_client.audio_duration_sec(audio_bytes)

        if duration > settings.meeting_max_duration_sec:
            raise StepFailed(
                FailedStep.TRANSCRIPT,
                f"This recording is {duration / 60:.0f} minutes long. The limit is {settings.meeting_max_duration_sec // 60} minutes.",
            )

        result = transcript_service.transcribe_audio(db, workspace_id, audio_bytes, None, "auto", attendee_ids)

        return duration, result.entries

    duration, entries = _guard(FailedStep.TRANSCRIPT, work)

    if not entries:
        raise StepFailed(FailedStep.TRANSCRIPT, "No speech was found in the recording.")

    meeting = meeting_repository.get(db, meeting_id)
    meeting_repository.get_audio(db, meeting_id).duration_sec = duration
    meeting_result_repository.replace_segments(db, meeting_id, _segment_rows(meeting_id, entries))
    meeting.transcribed_at = _now()
    db.commit()


def _segment_rows(meeting_id: UUID, entries: list[TranscriptEntry]) -> list[TranscriptSegment]:
    rows = []

    for position, entry in enumerate(entries, start=1):
        unknown_match = UNKNOWN_LABEL.fullmatch(entry.speaker_label)
        unknown_number = None

        if entry.user_id is not None:
            kind = SpeakerKind.MEMBER
        elif unknown_match:
            kind = SpeakerKind.UNKNOWN
            unknown_number = int(unknown_match.group(1))
        else:
            kind = SpeakerKind.UNCLEAR

        rows.append(
            TranscriptSegment(
                meeting_id=meeting_id,
                position=position,
                start_sec=entry.start,
                end_sec=entry.end,
                text=entry.text,
                language=SegmentLanguage(entry.language),
                speaker_kind=kind,
                speaker_user_id=entry.user_id,
                unknown_number=unknown_number,
                evidence={
                    "best_candidate_name": entry.best_candidate_name,
                    "best_score": entry.best_score,
                    "runner_up_name": entry.runner_up_name,
                    "runner_up_score": entry.runner_up_score,
                    "margin": entry.margin,
                    "pooled_seconds": entry.pooled_seconds,
                    "floor_applied": entry.floor_applied,
                },
            )
        )

    return rows


# --- step 2: summary -------------------------------------------------------------------------------


def _summary_step(db: Session, meeting_id: UUID) -> None:
    segments = meeting_result_repository.list_segments(db, meeting_id)

    if not segments:
        raise StepFailed(FailedStep.SUMMARY, "There is no transcript to summarize.")

    names = meeting_view.load_names(db, meeting_id, segments)
    attendees = meeting_repository.list_attendees(db, meeting_id)
    turns = [
        {"index": segment.position, "speaker": names.segment_speaker(segment).name, "start": segment.start_sec, "text": segment.text}
        for segment in segments
    ]

    db.commit()

    result = _guard(FailedStep.SUMMARY, lambda: summary_service.summarize_turns(turns, None))

    summary = Summary(
        meeting_id=meeting_id,
        engine=result.engine,
        model=result.model,
        attempts=result.attempts,
        parts=result.parts,
        dropped_decisions=result.dropped_decisions,
        dropped_action_items=result.dropped_action_items,
        sentences=[point.model_dump() for point in result.summary],
        key_points=[point.model_dump() for point in result.key_points],
    )
    decisions = []

    for position, decision in enumerate(result.decisions, start=1):
        attendee_id, unknown_number = _resolve_person(decision.decided_by, decision.unnamed_label, attendees)
        decisions.append(
            Decision(
                meeting_id=meeting_id,
                position=position,
                decision=decision.decision,
                quote=decision.quote,
                turns=decision.turns,
                decided_by_attendee_id=attendee_id,
                decided_by_unknown_number=unknown_number,
                warnings=decision.warnings,
            )
        )

    action_items = []

    for position, action in enumerate(result.action_items, start=1):
        attendee_id, unknown_number = _resolve_person(action.owner, action.unnamed_label, attendees)
        action_items.append(
            ActionItem(
                meeting_id=meeting_id,
                position=position,
                task=action.task,
                deadline_text=action.deadline,
                quote=action.quote,
                turns=action.turns,
                owner_attendee_id=attendee_id,
                owner_unknown_number=unknown_number,
                warnings=action.warnings,
            )
        )

    meeting_result_repository.replace_summary(db, meeting_id, summary, decisions, action_items)
    meeting_repository.get(db, meeting_id).summarized_at = _now()
    db.commit()


def _resolve_person(
    name: str | None, unnamed_label: str | None, attendees: list[tuple[MeetingAttendee, User | None]]
) -> tuple[UUID | None, int | None]:
    """Maps the name the summarizer gave to an attendee, or to an Unknown Speaker number so a later rename
    still reaches it. Anything that matches nobody, or more than one person, stays unidentified."""
    if unnamed_label:
        match = UNKNOWN_LABEL.fullmatch(unnamed_label)

        return (None, int(match.group(1))) if match else (None, None)

    if not name:
        return None, None

    wanted = " ".join(name.casefold().split())
    matches = []

    for attendee, user in attendees:
        attendee_name = user.display_name if user is not None else attendee.guest_name

        if attendee_name and " ".join(attendee_name.casefold().split()) == wanted:
            matches.append(attendee.id)

    return (matches[0], None) if len(matches) == 1 else (None, None)


# --- after a restart --------------------------------------------------------------------------------


def recover_interrupted(session_factory: SessionFactory) -> int:
    """Background work dies with the server. A meeting still marked processing at startup was cut off, so it is
    marked failed at the step it had reached, and can be retried. Returns how many were recovered."""
    with session_factory() as db:
        stuck = meeting_repository.list_processing(db)

        for meeting in stuck:
            meeting.status = MeetingStatus.FAILED
            meeting.failed_step = FailedStep.TRANSCRIPT if meeting.transcribed_at is None else FailedStep.SUMMARY
            meeting.failure_reason = "Processing was interrupted when the server restarted. Press retry."

        db.commit()

        return len(stuck)
