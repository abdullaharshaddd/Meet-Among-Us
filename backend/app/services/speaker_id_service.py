"""Works out who is talking in an uploaded clip. See docs/adr/0020-speaker-matching.md
for why only the workspace's own members are candidates and how unknown voices are numbered.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.core.config import SpeakerIdSettings, speaker_id_settings
from app.core.exceptions import ClipNotInWorkspaceError, ParticipantNotInWorkspaceError
from app.core.vectors import cosine_similarity, normalise
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.repositories import voiceprint_repository, workspace_member_repository
from app.schemas.enrollment import UploadUrlResponse
from app.schemas.speaker_id import IdentifyResponse, ParticipantChoice, SkippedVoiceprint, SpeakerTurn
from app.services import permissions
from app.services.enrollment_service import CONTENT_TYPES, UPLOAD_URL_EXPIRES_IN_SECONDS

def clip_prefix(workspace_id: UUID) -> str:
    return f"workspace-clips/{workspace_id}/"


def create_clip_upload_url(
    db: Session, user: User, workspace_id: UUID, audio_format: str
) -> UploadUrlResponse:
    permissions.require_member(db, workspace_id, user.id)

    audio_key = f"{clip_prefix(workspace_id)}{uuid4()}.{audio_format}"
    upload_url = storage.presign_put(
        audio_key,
        content_type=CONTENT_TYPES[audio_format],
        expires_in=UPLOAD_URL_EXPIRES_IN_SECONDS,
    )

    return UploadUrlResponse(
        upload_url=upload_url, audio_key=audio_key, expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS
    )


def split_by_model_version(
    rows: list[tuple[Voiceprint, User]], model_version: str
) -> tuple[list[Candidate], list[SkippedVoiceprint]]:
    candidates: list[Candidate] = []
    skipped: list[SkippedVoiceprint] = []

    for voiceprint, user in rows:
        if voiceprint.model_version != model_version:
            skipped.append(
                SkippedVoiceprint(
                    user_id=user.id,
                    name=user.display_name,
                    model_version=voiceprint.model_version,
                    reason=(
                        f"Enrolled with {voiceprint.model_version}, but this clip was "
                        f"embedded with {model_version}. Re-enroll."
                    ),
                )
            )
            continue

        candidates.append(
            Candidate(
                user_id=user.id,
                name=user.display_name,
                centroid=normalise(list(voiceprint.centroid)),
            )
        )

    return candidates, skipped


@dataclass
class Candidate:
    user_id: UUID
    name: str
    centroid: list[float]


@dataclass
class Run:
    """Neighbouring segments that point at the same person, pooled into one piece of
    evidence. Short slices score low on their own, so the decision is made on the pool."""

    start: float
    end: float
    seconds: float
    total: list[float]
    first_choice: UUID | None

    def vector(self) -> list[float]:
        return normalise(self.total)

    def add(self, segment: ml_client.SegmentResult, unit_vector: list[float]) -> None:
        self.end = segment.end
        self.seconds += segment.end - segment.start
        self.total = [a + b for a, b in zip(self.total, unit_vector)]


@dataclass
class UnknownGroup:
    number: int
    total: list[float]

    def mean(self) -> list[float]:
        return normalise(self.total)

    def add(self, vector: list[float]) -> None:
        self.total = [a + b for a, b in zip(self.total, vector)]


@dataclass
class LabelledRun:
    start: float
    end: float
    seconds: float
    user_id: UUID | None
    unknown_number: int | None
    label: str
    best_name: str | None
    best_score: float | None
    runner_up_name: str | None
    runner_up_score: float | None
    margin: float | None
    floor: float


def floor_for(seconds: float, settings: SpeakerIdSettings) -> float:
    return min(settings.floor_base + settings.floor_slope * seconds, settings.floor_cap)


def _scores(vector: list[float], candidates: list[Candidate]) -> dict[UUID, float]:
    return {candidate.user_id: cosine_similarity(vector, candidate.centroid) for candidate in candidates}


def pool_into_runs(
    segments: list[ml_client.SegmentResult], candidates: list[Candidate], settings: SpeakerIdSettings
) -> list[Run]:
    runs: list[Run] = []

    for index, segment in enumerate(segments):
        vector = normalise(segment.embedding)
        scores = _scores(vector, candidates)
        first_choice = max(scores, key=lambda user_id: scores[user_id]) if scores else None
        current = runs[-1] if runs else None

        # An unknown voice is nobody's best match for long, so the same first choice alone
        # is not enough to pool: the new slice must also sound like what is already pooled.
        # With no candidates there is nothing to pool by, so each segment stands alone.
        joins_current = (
            current is not None
            and first_choice is not None
            and current.first_choice == first_choice
            and cosine_similarity(vector, current.vector()) >= settings.unknown_group_threshold
        )

        if joins_current:
            current.add(segment, vector)
        else:
            runs.append(Run(segment.start, segment.end, segment.end - segment.start, list(vector), first_choice))

    return runs


def label_runs(runs: list[Run], candidates: list[Candidate], settings: SpeakerIdSettings) -> list[LabelledRun]:
    names = {candidate.user_id: candidate.name for candidate in candidates}
    unknown_groups: list[UnknownGroup] = []
    labelled: list[LabelledRun] = []

    for run in runs:
        vector = run.vector()
        ranked = sorted(_scores(vector, candidates).items(), key=lambda item: item[1], reverse=True)
        best_id, best_score = ranked[0] if ranked else (None, None)
        runner_up_id, runner_up_score = ranked[1] if len(ranked) > 1 else (None, None)
        margin = best_score - runner_up_score if runner_up_score is not None else None
        floor = floor_for(run.seconds, settings)

        # With a single candidate there is no runner-up, so the margin rule cannot apply.
        is_named = best_score is not None and best_score >= floor and (margin is None or margin >= settings.margin)

        fields = dict(
            start=run.start,
            end=run.end,
            seconds=run.seconds,
            best_name=names.get(best_id),
            best_score=best_score,
            runner_up_name=names.get(runner_up_id),
            runner_up_score=runner_up_score,
            margin=margin,
            floor=floor,
        )

        if is_named:
            labelled.append(LabelledRun(user_id=best_id, unknown_number=None, label=names[best_id], **fields))
            continue

        if run.seconds < settings.min_group_seconds:
            labelled.append(LabelledRun(user_id=None, unknown_number=None, label="Unclear", **fields))
            continue

        group = _closest_unknown_group(unknown_groups, vector, settings)

        if group is None:
            group = UnknownGroup(number=len(unknown_groups) + 1, total=[0.0] * len(vector))
            unknown_groups.append(group)

        group.add(vector)
        labelled.append(
            LabelledRun(user_id=None, unknown_number=group.number, label=f"Unknown Speaker {group.number}", **fields)
        )

    return labelled


def _closest_unknown_group(
    groups: list[UnknownGroup], vector: list[float], settings: SpeakerIdSettings
) -> UnknownGroup | None:
    best_group = None
    best_score = settings.unknown_group_threshold

    for group in groups:
        score = cosine_similarity(vector, group.mean())

        if score >= best_score:
            best_group = group
            best_score = score

    return best_group


def merge_into_turns(labelled: list[LabelledRun]) -> list[SpeakerTurn]:
    groups: list[list[LabelledRun]] = []

    for run in labelled:
        same_speaker = (
            groups and groups[-1][-1].user_id == run.user_id and groups[-1][-1].unknown_number == run.unknown_number
        )

        if same_speaker:
            groups[-1].append(run)
        else:
            groups.append([run])

    return [_build_turn(group) for group in groups]


def _weighted_mean(group: list[LabelledRun], attribute: str) -> float | None:
    values = [(getattr(run, attribute), run.seconds) for run in group if getattr(run, attribute) is not None]

    if not values:
        return None

    return sum(value * seconds for value, seconds in values) / sum(seconds for _, seconds in values)


def _build_turn(group: list[LabelledRun]) -> SpeakerTurn:
    first = group[0]

    return SpeakerTurn(
        speaker_label=first.label,
        user_id=first.user_id,
        start=first.start,
        end=group[-1].end,
        best_candidate_name=first.best_name,
        best_score=_weighted_mean(group, "best_score"),
        runner_up_name=first.runner_up_name,
        runner_up_score=_weighted_mean(group, "runner_up_score"),
        margin=_weighted_mean(group, "margin"),
        pooled_seconds=sum(run.seconds for run in group),
        floor_applied=_weighted_mean(group, "floor") or 0.0,
    )


def require_clip_access(db: Session, user: User, workspace_id: UUID, audio_key: str) -> None:
    permissions.require_member(db, workspace_id, user.id)

    # Without this, any member could point /identify at any object in the bucket,
    # including someone else's enrollment recording.
    if not audio_key.startswith(clip_prefix(workspace_id)):
        raise ClipNotInWorkspaceError("That audio wasn't uploaded for this workspace.")


def require_participants(db: Session, workspace_id: UUID, participant_user_ids: list[UUID] | None) -> set[UUID] | None:
    """None means no restriction. Anyone named must belong to this workspace, so a caller cannot
    use the list to probe for people outside it."""
    if participant_user_ids is None:
        return None

    wanted = set(participant_user_ids)
    members = {member.user_id for member, _ in workspace_member_repository.list_with_users(db, workspace_id)}
    outsiders = wanted - members

    if outsiders:
        raise ParticipantNotInWorkspaceError(
            "These participants are not members of this workspace: " + ", ".join(sorted(str(i) for i in outsiders))
        )

    return wanted


def restrict_to_participants(
    rows: list[tuple[Voiceprint, User]], participant_ids: set[UUID] | None
) -> list[tuple[Voiceprint, User]]:
    if participant_ids is None:
        return rows

    return [(voiceprint, user) for voiceprint, user in rows if user.id in participant_ids]


def identify_audio(
    db: Session,
    workspace_id: UUID,
    audio_bytes: bytes,
    settings: SpeakerIdSettings,
    participant_ids: set[UUID] | None = None,
) -> IdentifyResponse:
    result = ml_client.find_segments(audio_bytes, settings)
    # A participant who is a member but never enrolled has no voiceprint, so cannot be matched.
    rows = restrict_to_participants(voiceprint_repository.list_for_workspace(db, workspace_id), participant_ids)
    candidates, skipped = split_by_model_version(rows, result.model_version)
    runs = pool_into_runs(result.segments, candidates, settings)
    labelled = label_runs(runs, candidates, settings)

    return IdentifyResponse(
        model_version=result.model_version,
        duration_sec=result.duration_sec,
        turns=merge_into_turns(labelled),
        skipped_voiceprints=skipped,
    )


def identify(
    db: Session,
    user: User,
    workspace_id: UUID,
    audio_key: str,
    participant_user_ids: list[UUID] | None = None,
    settings: SpeakerIdSettings = speaker_id_settings,
) -> IdentifyResponse:
    require_clip_access(db, user, workspace_id, audio_key)
    participant_ids = require_participants(db, workspace_id, participant_user_ids)

    return identify_audio(db, workspace_id, storage.get_object_bytes(audio_key), settings, participant_ids)


def list_participant_choices(db: Session, user: User, workspace_id: UUID) -> list[ParticipantChoice]:
    permissions.require_member(db, workspace_id, user.id)

    return [
        ParticipantChoice(
            user_id=member_user.id,
            display_name=member_user.display_name,
            enrollment_status=member_user.enrollment_status.value,
        )
        for _, member_user in workspace_member_repository.list_with_users(db, workspace_id)
    ]
