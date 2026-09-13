from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.voiceprint import Voiceprint


def get_by_user_id(db: Session, user_id: UUID) -> Voiceprint | None:
    return db.execute(select(Voiceprint).where(Voiceprint.user_id == user_id)).scalar_one_or_none()


def upsert(
    db: Session,
    *,
    user_id: UUID,
    centroid: list[float],
    intra_speaker_variance: float,
    sample_count: int,
    model_version: str,
) -> Voiceprint:
    """Update, not just insert — a user who resets and re-enrolls hits this again
    for the same user_id, which the unique constraint on user_id would otherwise
    reject as a duplicate insert."""
    existing = get_by_user_id(db, user_id)
    if existing is not None:
        existing.centroid = centroid
        existing.intra_speaker_variance = intra_speaker_variance
        existing.sample_count = sample_count
        existing.model_version = model_version
        db.commit()
        db.refresh(existing)
        return existing

    voiceprint = Voiceprint(
        user_id=user_id,
        centroid=centroid,
        intra_speaker_variance=intra_speaker_variance,
        sample_count=sample_count,
        model_version=model_version,
    )
    db.add(voiceprint)
    db.commit()
    db.refresh(voiceprint)
    return voiceprint


def delete_by_user_id(db: Session, user_id: UUID) -> None:
    db.execute(delete(Voiceprint).where(Voiceprint.user_id == user_id))
    db.commit()
