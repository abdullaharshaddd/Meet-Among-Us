"""Voice enrollment: turns three passage recordings into one voiceprint. See
docs/adr/0012-three-passage-bilingual-enrollment.md for why three languages, and
docs/adr/0013-enrollment-quality-gate.md for why a bad sample is rejected
outright rather than stored with a warning.

`storage` and `ml_client` are imported as modules, not their individual
functions, purely so tests can monkeypatch e.g. `enrollment_service.ml_client.
embed_sample` without touching the real R2/ML network calls — same reasoning as
ml/ml/quality.py stubbing `quality.vad`.
"""

from __future__ import annotations

import math
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.core.exceptions import EnrollmentAlreadyCompleteError
from app.models.enrollment_sample import EnrollmentLanguage, EnrollmentSample
from app.models.user import EnrollmentStatus, User
from app.repositories import enrollment_sample_repository, user_repository, voiceprint_repository
from app.schemas.enrollment import (
    EnrollmentStatusResponse,
    PassageStatus,
    SubmitSampleResponse,
    UploadUrlResponse,
)

MODEL_VERSION = "ecapa-voxceleb-v1"
UPLOAD_URL_EXPIRES_IN_SECONDS = 900

# A passage rejected this many times in a row, with no acceptance since, flips
# enrollment_status to 'failed' — a UX signal to stop retrying blindly and show
# help text, not a hard stop (any later acceptance clears it). Counted from
# enrollment_samples rows directly; no separate counter column needed.
CONSECUTIVE_REJECTION_LIMIT = 3

# Mirrors ml/ml/quality.py's REASONS dict. Duplicated rather than imported —
# /ml and /backend are separate uv environments with no shared package (see
# ADR-0014) — but these four short, stable strings are cheaper to hand-keep in
# sync than to introduce one for. Re-deriving from (code, speech_duration_sec)
# here, rather than persisting the formatted sentence, means an old rejected
# row still renders correctly if the copy is ever reworded.
REJECTION_MESSAGES: dict[str, str] = {
    "NEAR_SILENT": "We couldn't hear anything — check your mic and try again.",
    "CLIPPED": "Your voice was too loud for the mic — move back a little.",
    "SPEECH_TOO_SHORT": "We only caught {speech_duration_sec:.1f} seconds of speech — read the whole passage.",
    "TOO_NOISY": "Too much background noise — try a quieter room.",
}


def _reason_message(reason_code: str, speech_duration_sec: float) -> str:
    return REJECTION_MESSAGES[reason_code].format(speech_duration_sec=speech_duration_sec)


def create_upload_url(user: User, language: EnrollmentLanguage) -> UploadUrlResponse:
    # FLAC per CLAUDE.md's locked "record WAV, upload FLAC" decision — the mobile
    # client transcodes before this URL ever gets used.
    audio_key = f"enrollment/{user.id}/{language.value}/{uuid4()}.flac"
    upload_url = storage.presign_put(
        audio_key, content_type="audio/flac", expires_in=UPLOAD_URL_EXPIRES_IN_SECONDS
    )
    return UploadUrlResponse(
        upload_url=upload_url, audio_key=audio_key, expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS
    )


def submit_sample(
    db: Session, user: User, language: EnrollmentLanguage, audio_key: str
) -> SubmitSampleResponse:
    if user.enrollment_status == EnrollmentStatus.COMPLETE:
        raise EnrollmentAlreadyCompleteError(
            "Enrollment is already complete — reset via DELETE /enrollment to re-enroll"
        )

    audio_bytes = storage.get_object_bytes(audio_key)
    result = ml_client.embed_sample(audio_bytes)

    enrollment_sample_repository.create(
        db,
        user_id=user.id,
        audio_key=audio_key,
        language=language,
        duration_sec=result.duration_sec,
        snr_db=result.snr_db,
        speech_duration_sec=result.speech_duration_sec,
        embedding=result.embedding,
        accepted=result.accepted,
        rejection_reason=result.reason_code,
    )

    if user.enrollment_status == EnrollmentStatus.NOT_STARTED:
        user = user_repository.set_enrollment_status(db, user, EnrollmentStatus.IN_PROGRESS)

    samples = enrollment_sample_repository.list_by_user_desc(db, user.id)

    if _consecutive_rejections(samples) >= CONSECUTIVE_REJECTION_LIMIT:
        user = user_repository.set_enrollment_status(db, user, EnrollmentStatus.FAILED)
    elif result.accepted:
        accepted = _latest_accepted_per_language(samples)
        if len(accepted) == len(EnrollmentLanguage):
            centroid, variance = _compute_centroid([s.embedding for s in accepted.values()])
            voiceprint_repository.upsert(
                db,
                user_id=user.id,
                centroid=centroid,
                intra_speaker_variance=variance,
                sample_count=len(accepted),
                model_version=MODEL_VERSION,
            )
            user = user_repository.set_enrollment_status(db, user, EnrollmentStatus.COMPLETE)
        elif user.enrollment_status == EnrollmentStatus.FAILED:
            # An acceptance always breaks a losing streak, even if the set of
            # three passages still isn't complete.
            user = user_repository.set_enrollment_status(db, user, EnrollmentStatus.IN_PROGRESS)

    reason_message = (
        _reason_message(result.reason_code, result.speech_duration_sec) if result.reason_code else None
    )
    return SubmitSampleResponse(
        accepted=result.accepted,
        reason_code=result.reason_code,
        reason_message=reason_message,
        enrollment_status=user.enrollment_status,
    )


def get_status(db: Session, user: User) -> EnrollmentStatusResponse:
    samples = enrollment_sample_repository.list_by_user_desc(db, user.id)
    latest_by_language: dict[EnrollmentLanguage, EnrollmentSample] = {}
    for sample in samples:
        latest_by_language.setdefault(sample.language, sample)

    passages = []
    for language in EnrollmentLanguage:
        sample = latest_by_language.get(language)
        if sample is None:
            passages.append(
                PassageStatus(language=language, state="not_attempted", reason_code=None, reason_message=None)
            )
        elif sample.accepted:
            passages.append(
                PassageStatus(language=language, state="accepted", reason_code=None, reason_message=None)
            )
        else:
            passages.append(
                PassageStatus(
                    language=language,
                    state="rejected",
                    reason_code=sample.rejection_reason,
                    reason_message=_reason_message(sample.rejection_reason, sample.speech_duration_sec),
                )
            )

    return EnrollmentStatusResponse(enrollment_status=user.enrollment_status, passages=passages)


def reset_enrollment(db: Session, user: User) -> None:
    """Hard reset: every sample row, the voiceprint, and their R2 objects are
    gone — there is no soft/undo path, matching the spec's 'hard reset'."""
    audio_keys = enrollment_sample_repository.delete_by_user_id(db, user.id)
    voiceprint_repository.delete_by_user_id(db, user.id)
    storage.delete_objects(audio_keys)
    user_repository.set_enrollment_status(db, user, EnrollmentStatus.NOT_STARTED)


def _consecutive_rejections(samples_desc: list[EnrollmentSample]) -> int:
    """Newest-first rejections until the first acceptance — an acceptance always
    breaks the streak, per the status state machine above."""
    count = 0
    for sample in samples_desc:
        if sample.accepted:
            break
        count += 1
    return count


def _latest_accepted_per_language(
    samples_desc: list[EnrollmentSample],
) -> dict[EnrollmentLanguage, EnrollmentSample]:
    latest: dict[EnrollmentLanguage, EnrollmentSample] = {}
    for sample in samples_desc:
        if sample.accepted:
            latest.setdefault(sample.language, sample)
    return latest


def _compute_centroid(embeddings: list[list[float]]) -> tuple[list[float], float]:
    """L2-normalised mean, plus the mean pairwise cosine distance across the
    inputs as an empirical spread measurement (ADR-0012). Plain Python, not
    numpy — three 192-dim vectors is nowhere near where that trade pays off, and
    the backend has no other use for a numpy dependency."""
    dim = len(embeddings[0])
    mean = [sum(vector[i] for vector in embeddings) / len(embeddings) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in mean))
    centroid = [x / norm for x in mean] if norm > 0 else mean

    def cosine_distance(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 1.0
        return 1 - dot / (norm_a * norm_b)

    pairs = [(i, j) for i in range(len(embeddings)) for j in range(i + 1, len(embeddings))]
    variance = sum(cosine_distance(embeddings[i], embeddings[j]) for i, j in pairs) / len(pairs)
    return centroid, variance
