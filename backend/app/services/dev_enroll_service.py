"""Diagnostics and cross-user listing for the /dev/enroll browser harness only.

Deliberately kept separate from enrollment_service.py rather than adding these as
methods there: nothing in here is part of the real enrollment contract (mobile app,
Milestone 1 spec), and keeping it isolated to this one file plus app/routers/dev_enroll.py
means removing the dev tool later is a two-file deletion, not a diff against
production logic. See docs/adr/0015-dev-enrollment-harness.md.
"""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enrollment_sample import EnrollmentLanguage, EnrollmentSample
from app.models.user import User
from app.repositories import enrollment_sample_repository, voiceprint_repository


def _l2_norm(vector: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vector))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a, norm_b = _l2_norm(a), _l2_norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _latest_by_language(samples_desc: list[EnrollmentSample]) -> dict[EnrollmentLanguage, EnrollmentSample]:
    latest: dict[EnrollmentLanguage, EnrollmentSample] = {}
    for sample in samples_desc:
        latest.setdefault(sample.language, sample)
    return latest


def list_sample_measurements(db: Session, user: User) -> list[dict]:
    """Per-language latest sample, including the numbers the real
    SubmitSampleResponse never returns (duration, speech duration, SNR) — the
    harness shows these next to the plain-English rejection message so a
    rejection is diagnosable, not just a name."""
    samples = enrollment_sample_repository.list_by_user_desc(db, user.id)
    latest = _latest_by_language(samples)
    return [
        {
            "language": language.value,
            "accepted": sample.accepted,
            "reason_code": sample.rejection_reason,
            "duration_sec": sample.duration_sec,
            "speech_duration_sec": sample.speech_duration_sec,
            "snr_db": sample.snr_db,
        }
        for language, sample in latest.items()
    ]


def get_diagnostics(db: Session, user: User) -> dict | None:
    """None until all three passages are accepted and a voiceprint exists —
    the caller turns that into a 404, not an empty-but-200 response."""
    voiceprint = voiceprint_repository.get_by_user_id(db, user.id)
    if voiceprint is None:
        return None

    samples = enrollment_sample_repository.list_by_user_desc(db, user.id)
    accepted = {lang: s for lang, s in _latest_by_language(samples).items() if s.accepted}

    centroid = voiceprint.centroid
    per_passage = [
        {"language": language.value, "similarity_to_centroid": _cosine_similarity(sample.embedding, centroid)}
        for language, sample in accepted.items()
    ]

    cross_language_similarity_en_ur = None
    if EnrollmentLanguage.EN in accepted and EnrollmentLanguage.UR in accepted:
        cross_language_similarity_en_ur = _cosine_similarity(
            accepted[EnrollmentLanguage.EN].embedding, accepted[EnrollmentLanguage.UR].embedding
        )

    return {
        # Should be 1.0 — _compute_centroid L2-normalises before storing. A value
        # off 1.0 here means that normalisation broke, and every cosine similarity
        # computed against this centroid downstream (meeting-time verification) is
        # silently wrong, not just off by a little.
        "centroid_l2_norm": _l2_norm(centroid),
        "intra_speaker_variance": voiceprint.intra_speaker_variance,
        "sample_count": voiceprint.sample_count,
        "model_version": voiceprint.model_version,
        "per_passage_similarity": per_passage,
        "cross_language_similarity_en_ur": cross_language_similarity_en_ur,
    }


def list_admin_users(db: Session) -> list[dict]:
    """Every user in the database, enrolled or not — the six-speaker Urdu
    separation experiment needs to see who still hasn't finished. Unscoped by
    design: there is no per-workspace concept yet to scope it to, and this
    endpoint only exists behind DEV_TOOLS_ENABLED in the first place."""
    users = db.execute(select(User)).scalars().all()
    rows = []
    for user in users:
        samples = enrollment_sample_repository.list_by_user_desc(db, user.id)
        voiceprint = voiceprint_repository.get_by_user_id(db, user.id)
        rows.append(
            {
                "email": user.email,
                "display_name": user.display_name,
                "enrollment_status": user.enrollment_status.value,
                "accepted_sample_count": sum(1 for s in samples if s.accepted),
                "total_sample_count": len(samples),
                "intra_speaker_variance": voiceprint.intra_speaker_variance if voiceprint else None,
                "centroid_l2_norm": _l2_norm(voiceprint.centroid) if voiceprint else None,
            }
        )
    return rows
