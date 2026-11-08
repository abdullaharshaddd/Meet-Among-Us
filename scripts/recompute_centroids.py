"""One-off: rebuild every stored voiceprint centroid with the ADR-0020 convention
(normalise each enrollment embedding, average, normalise again).

Early voiceprints averaged the raw embeddings. This recomputes them from the
embeddings already saved in enrollment_samples and prints how far each centroid moved.

Run with:
    cd backend && uv run python ../scripts/recompute_centroids.py
"""

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.vectors import cosine_similarity
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.services import enrollment_service


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(User, Voiceprint).join(Voiceprint, Voiceprint.user_id == User.id).order_by(User.email)
        ).all()

        for user, voiceprint in rows:
            result = enrollment_service.rebuild_centroid(db, user.id)

            if result is None:
                print(f"{user.display_name}: no voiceprint")
                continue

            old_centroid, new_centroid = result
            similarity = cosine_similarity(old_centroid, new_centroid)
            print(f"{user.display_name} <{user.email}>: old vs new centroid cosine = {similarity:.6f}")


if __name__ == "__main__":
    main()
