"""Downloads each enrolled user's accepted enrollment recordings (and the embeddings the
ML service stored for them) into a local folder, for scripts/segment_length_study.py.

The folder holds people's voices. Keep it outside the repo.

Run with:
    cd backend && PYTHONPATH=. uv run python ../scripts/export_enrollment_audio.py OUT_DIR
"""

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.core import storage
from app.core.db import SessionLocal
from app.models.enrollment_sample import EnrollmentSample
from app.models.user import User
from app.repositories import enrollment_sample_repository, voiceprint_repository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", type=Path)
    arguments = parser.parse_args()
    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    with SessionLocal() as db:
        users = db.scalars(select(User).order_by(User.email)).all()

        for user in users:
            voiceprint = voiceprint_repository.get_by_user_id(db, user.id)

            if voiceprint is None:
                continue

            latest: dict[str, EnrollmentSample] = {}

            for sample in enrollment_sample_repository.list_by_user_desc(db, user.id):
                if sample.accepted:
                    latest.setdefault(sample.language.value, sample)

            for language, sample in latest.items():
                extension = sample.audio_key.rsplit(".", 1)[1]
                file_name = f"{user.display_name}_{language}.{extension}"
                (arguments.out_dir / file_name).write_bytes(storage.get_object_bytes(sample.audio_key))
                manifest.append(
                    {
                        "user": user.display_name,
                        "language": language,
                        "file": file_name,
                        "stored_embedding": list(sample.embedding),
                        "stored_centroid": list(voiceprint.centroid),
                    }
                )

    (arguments.out_dir / "manifest.json").write_text(json.dumps(manifest))
    print(f"exported {len(manifest)} samples to {arguments.out_dir}")


if __name__ == "__main__":
    main()
