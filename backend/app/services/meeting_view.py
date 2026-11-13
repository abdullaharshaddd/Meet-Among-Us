"""Turns stored meeting rows into the responses the app shows, with every name already worked out.

The app never has to know about renames or deleted accounts: a segment's speaker, a citation's speaker and an
action item's owner all arrive as a name. See docs/DATA_MODEL.md.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.meeting import ConsentRecord, Meeting, MeetingAttendee, MeetingStatus
from app.models.meeting_result import ActionItem, SpeakerKind, SpeakerRename, TranscriptSegment
from app.models.user import EnrollmentStatus, User
from app.repositories import meeting_repository, meeting_result_repository, user_repository
from app.schemas.meeting import (
    ActionItemResponse,
    AttendeeResponse,
    AudioResponse,
    CitationResponse,
    ConsentResponse,
    DecisionResponse,
    MeetingDetailResponse,
    MeetingStatusResponse,
    SegmentResponse,
    SpeakerRef,
    SummaryPointResponse,
    SummaryResponse,
)

FORMER_MEMBER = "Former member"
OWNER_NOT_IDENTIFIED = "owner not identified"
SPEAKER_NOT_IDENTIFIED = "speaker not identified"


class MeetingNames:
    """Works out what to call each person in one meeting."""

    def __init__(
        self,
        attendees: list[tuple[MeetingAttendee, User | None]],
        renames: list[SpeakerRename],
        extra_users: list[User] = (),
    ) -> None:
        self.attendee_by_id = {attendee.id: (attendee, user) for attendee, user in attendees}
        self.attendee_by_user_id = {attendee.user_id: attendee for attendee, _ in attendees if attendee.user_id}
        self.rename_by_number = {rename.unknown_number: rename for rename in renames}
        self.user_names = {user.id: user.display_name for _, user in attendees if user is not None}
        self.user_names.update({user.id: user.display_name for user in extra_users})

    def attendee_name(self, attendee_id: UUID) -> str:
        attendee, user = self.attendee_by_id[attendee_id]

        if user is not None:
            return user.display_name

        return attendee.guest_name or FORMER_MEMBER

    def _attendee_ref(self, attendee_id: UUID, unknown_number: int | None) -> SpeakerRef:
        attendee, user = self.attendee_by_id[attendee_id]

        if user is not None:
            kind = "member"
        elif attendee.guest_name:
            kind = "guest"
        else:
            kind = "former_member"

        return SpeakerRef(
            kind=kind,
            name=self.attendee_name(attendee_id),
            user_id=attendee.user_id,
            attendee_id=attendee.id,
            unknown_number=unknown_number,
        )

    def segment_speaker(self, segment: TranscriptSegment) -> SpeakerRef:
        if segment.speaker_kind == SpeakerKind.UNCLEAR:
            return SpeakerRef(kind="unclear", name="Unclear", user_id=None, attendee_id=None, unknown_number=None)

        if segment.speaker_kind == SpeakerKind.UNKNOWN:
            rename = self.rename_by_number.get(segment.unknown_number)

            if rename is not None and rename.attendee_id in self.attendee_by_id:
                return self._attendee_ref(rename.attendee_id, segment.unknown_number)

            return SpeakerRef(
                kind="unknown",
                name=f"Unknown Speaker {segment.unknown_number}",
                user_id=None,
                attendee_id=None,
                unknown_number=segment.unknown_number,
            )

        if segment.speaker_user_id is None:
            return SpeakerRef(kind="former_member", name=FORMER_MEMBER, user_id=None, attendee_id=None, unknown_number=None)

        attendee = self.attendee_by_user_id.get(segment.speaker_user_id)
        name = self.user_names.get(segment.speaker_user_id, FORMER_MEMBER)

        return SpeakerRef(
            kind="member",
            name=name,
            user_id=segment.speaker_user_id,
            attendee_id=attendee.id if attendee else None,
            unknown_number=None,
        )

    def person(self, attendee_id: UUID | None, unknown_number: int | None, nobody: str) -> str:
        """Who an owner or decider is. An unnamed voice that nobody renamed reads as `nobody`, not as a label."""
        if attendee_id in self.attendee_by_id:
            return self.attendee_name(attendee_id)

        rename = self.rename_by_number.get(unknown_number) if unknown_number is not None else None

        if rename is not None and rename.attendee_id in self.attendee_by_id:
            return self.attendee_name(rename.attendee_id)

        return nobody


def load_names(db: Session, meeting_id: UUID, segments: list[TranscriptSegment]) -> MeetingNames:
    attendees = meeting_repository.list_attendees(db, meeting_id)
    renames = meeting_result_repository.list_renames(db, meeting_id)
    known = {user.id for _, user in attendees if user is not None}
    missing = [segment.speaker_user_id for segment in segments if segment.speaker_user_id and segment.speaker_user_id not in known]

    return MeetingNames(attendees, renames, user_repository.get_many(db, list(set(missing))))


def waiting_for_consent(
    attendees: list[tuple[MeetingAttendee, User | None]], consents: list[ConsentRecord]
) -> list[str]:
    """Names of attendees who have not agreed. Someone who answered no is listed too, marked as declined."""
    answers = {record.attendee_id: record for record in consents}
    waiting = []

    for attendee, user in attendees:
        name = user.display_name if user is not None else (attendee.guest_name or FORMER_MEMBER)
        record = answers.get(attendee.id)

        if record is None:
            waiting.append(name)
        elif not record.granted:
            waiting.append(f"{name} (declined)")

    return waiting


def _citations(turns: list[int], segments_by_position: dict[int, TranscriptSegment], names: MeetingNames) -> list[CitationResponse]:
    citations = []

    for number in sorted(set(turns)):
        segment = segments_by_position.get(number)

        if segment is not None:
            citations.append(
                CitationResponse(
                    turn_number=number, start=segment.start_sec, speaker_name=names.segment_speaker(segment).name
                )
            )

    return citations


def action_item_response(
    item: ActionItem, segments_by_position: dict[int, TranscriptSegment], names: MeetingNames
) -> ActionItemResponse:
    return ActionItemResponse(
        id=item.id,
        task=item.task,
        owner=names.person(item.owner_attendee_id, item.owner_unknown_number, OWNER_NOT_IDENTIFIED),
        deadline_text=item.deadline_text,
        quote=item.quote,
        citations=_citations(item.turns, segments_by_position, names),
        warnings=item.warnings,
        done=item.done_at is not None,
        done_at=item.done_at,
    )


def _summary_response(
    db: Session, meeting_id: UUID, segments_by_position: dict[int, TranscriptSegment], names: MeetingNames
) -> SummaryResponse | None:
    summary = meeting_result_repository.get_summary(db, meeting_id)

    if summary is None:
        return None

    def point(raw: dict) -> SummaryPointResponse:
        return SummaryPointResponse(
            text=raw["text"],
            citations=_citations(raw["turns"], segments_by_position, names),
            warnings=raw.get("warnings", []),
        )

    decisions = [
        DecisionResponse(
            id=decision.id,
            decision=decision.decision,
            decided_by=names.person(decision.decided_by_attendee_id, decision.decided_by_unknown_number, SPEAKER_NOT_IDENTIFIED),
            quote=decision.quote,
            citations=_citations(decision.turns, segments_by_position, names),
            warnings=decision.warnings,
        )
        for decision in meeting_result_repository.list_decisions(db, meeting_id)
    ]
    action_items = [
        action_item_response(item, segments_by_position, names)
        for item in meeting_result_repository.list_action_items(db, meeting_id)
    ]

    return SummaryResponse(
        engine=summary.engine,
        model=summary.model,
        parts=summary.parts,
        dropped_decisions=summary.dropped_decisions,
        dropped_action_items=summary.dropped_action_items,
        sentences=[point(raw) for raw in summary.sentences],
        key_points=[point(raw) for raw in summary.key_points],
        decisions=decisions,
        action_items=action_items,
    )


def _host_name(db: Session, meeting: Meeting) -> str:
    host = user_repository.get_by_id(db, meeting.host_user_id) if meeting.host_user_id else None

    return host.display_name if host else FORMER_MEMBER


def build_detail(db: Session, meeting: Meeting, viewer_id: UUID) -> MeetingDetailResponse:
    attendees = meeting_repository.list_attendees(db, meeting.id)
    consents = meeting_repository.list_consents(db, meeting.id)
    consent_by_attendee = {record.attendee_id: record for record in consents}
    segments = meeting_result_repository.list_segments(db, meeting.id)
    segments_by_position = {segment.position: segment for segment in segments}
    names = load_names(db, meeting.id, segments)
    audio = meeting_repository.get_audio(db, meeting.id)
    waiting = waiting_for_consent(attendees, consents)
    attendee_responses = []
    warnings = []

    for attendee, user in attendees:
        record = consent_by_attendee.get(attendee.id)
        enrolled = None

        if user is not None:
            enrolled = user.enrollment_status == EnrollmentStatus.COMPLETE

            if not enrolled:
                warnings.append(f"{user.display_name} hasn't enrolled, so their speech can't be named automatically.")

        attendee_responses.append(
            AttendeeResponse(
                id=attendee.id,
                kind="member" if user is not None else ("guest" if attendee.guest_name else "former_member"),
                name=user.display_name if user is not None else (attendee.guest_name or FORMER_MEMBER),
                user_id=attendee.user_id,
                is_host=attendee.user_id is not None and attendee.user_id == meeting.host_user_id,
                is_me=attendee.user_id is not None and attendee.user_id == viewer_id,
                enrolled=enrolled,
                consent=ConsentResponse(granted=record.granted, method=record.method, granted_at=record.granted_at)
                if record
                else None,
            )
        )

    return MeetingDetailResponse(
        id=meeting.id,
        workspace_id=meeting.workspace_id,
        title=meeting.title,
        status=meeting.status,
        failed_step=meeting.failed_step,
        failure_reason=meeting.failure_reason,
        host_name=_host_name(db, meeting),
        is_host=meeting.host_user_id == viewer_id,
        created_at=meeting.created_at,
        attendees=attendee_responses,
        warnings=warnings,
        consent_ready=not waiting,
        waiting_for_consent=waiting,
        audio=AudioResponse(
            uploaded=audio is not None and audio.uploaded_at is not None,
            uploaded_at=audio.uploaded_at if audio else None,
            size_bytes=audio.size_bytes if audio else None,
            duration_sec=audio.duration_sec if audio else None,
        ),
        transcript=[
            SegmentResponse(
                position=segment.position,
                start=segment.start_sec,
                end=segment.end_sec,
                text=segment.text,
                language=segment.language.value,
                speaker=names.segment_speaker(segment),
            )
            for segment in segments
        ],
        summary=_summary_response(db, meeting.id, segments_by_position, names),
    )


def build_status(db: Session, meeting: Meeting) -> MeetingStatusResponse:
    attendees = meeting_repository.list_attendees(db, meeting.id)
    consents = meeting_repository.list_consents(db, meeting.id)
    audio = meeting_repository.get_audio(db, meeting.id)

    return MeetingStatusResponse(
        id=meeting.id,
        status=meeting.status,
        failed_step=meeting.failed_step,
        failure_reason=meeting.failure_reason,
        audio_uploaded=audio is not None and audio.uploaded_at is not None,
        consent_ready=not waiting_for_consent(attendees, consents),
        transcript_ready=meeting.transcribed_at is not None,
        summary_ready=meeting.summarized_at is not None,
    )


def is_editable(meeting: Meeting) -> bool:
    return meeting.status in (MeetingStatus.WAITING_FOR_AUDIO, MeetingStatus.FAILED)
