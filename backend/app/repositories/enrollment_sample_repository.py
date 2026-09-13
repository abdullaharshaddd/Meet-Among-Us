from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.enrollment_sample import EnrollmentLanguage, EnrollmentSample


def create(
    db: Session,
    *,
    user_id: UUID,
    audio_key: str,
    language: EnrollmentLanguage,
    duration_sec: float,
    snr_db: float,
    speech_duration_sec: float,
    embedding: list[float] | None,
    accepted: bool,
    rejection_reason: str | None,
) -> EnrollmentSample:
    sample = EnrollmentSample(
        user_id=user_id,
        audio_key=audio_key,
        language=language,
        duration_sec=duration_sec,
        snr_db=snr_db,
        speech_duration_sec=speech_duration_sec,
        embedding=embedding,
        accepted=accepted,
        rejection_reason=rejection_reason,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def list_by_user_desc(db: Session, user_id: UUID) -> list[EnrollmentSample]:
    """Newest first — both the three-strikes count and the reset's audio-key
    collection want this order (the former; the latter doesn't care but there's
    no reason for a second query shape).

    Tiebroken by id, not just created_at: Postgres's now() is fixed for the
    whole transaction, so rows inserted in quick succession (or, as happened in
    this suite's savepoint-per-test setup, in the same transaction entirely)
    can share one timestamp. UUIDv7 ids are time-ordered by design (see
    docs/adr/0004-uuid7-and-citext.md), so they break the tie correctly.
    """
    return list(
        db.execute(
            select(EnrollmentSample)
            .where(EnrollmentSample.user_id == user_id)
            .order_by(EnrollmentSample.created_at.desc(), EnrollmentSample.id.desc())
        ).scalars()
    )


def delete_by_user_id(db: Session, user_id: UUID) -> list[str]:
    """Returns the deleted rows' audio_keys so the caller can clean up R2 —
    once the DELETE runs there's no other way to know what they were."""
    keys = [s.audio_key for s in list_by_user_desc(db, user_id)]
    db.execute(delete(EnrollmentSample).where(EnrollmentSample.user_id == user_id))
    db.commit()
    return keys
