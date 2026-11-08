"""One command to re-derive the speaker-matching numbers, for example after re-enrollment
or when new people have enrolled.

    python scripts/rerun_segment_length_study.py [--exclude-pair mubashra,Vaniya]

It downloads every enrolled user's accepted recordings into a temporary folder (the folder
holds people's voices, so it is deleted afterwards), then runs segment_length_study.py with
the floor and cutting parameters currently in the backend config, and rewrites
docs/evaluation/segment_length.md and .png.
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exclude-pair", help="two display names, e.g. mubashra,Vaniya")
    arguments = parser.parse_args()

    data_dir = Path(tempfile.mkdtemp(prefix="enrollment_audio_"))
    backend_environment = {**os.environ, "PYTHONPATH": "."}

    try:
        subprocess.run(
            ["uv", "run", "python", "../scripts/export_enrollment_audio.py", str(data_dir)],
            cwd=ROOT / "backend",
            env=backend_environment,
            check=True,
        )

        parameters = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "import json; from app.core.config import speaker_id_settings as s; "
                "print(json.dumps({k: getattr(s, k) for k in ('merge_gap_sec', 'floor_base', 'floor_slope', 'floor_cap')}))",
            ],
            cwd=ROOT / "backend",
            env=backend_environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().splitlines()[-1]

        command = [
            "uv", "run", "--with", "matplotlib", "python", "../scripts/segment_length_study.py",
            str(data_dir), "--params-json", parameters,
        ]

        if arguments.exclude_pair:
            command += ["--exclude-pair", arguments.exclude_pair]

        subprocess.run(command, cwd=ROOT / "ml", check=True)
    finally:
        shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
