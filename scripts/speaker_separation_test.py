"""Task 4 — does ECAPA-TDNN separate speakers across languages?

The whole speaker-attribution architecture assumes that two recordings of the
same person — one in English, one in Urdu — land closer together in embedding
space than two recordings of different people. ECAPA-TDNN was trained on
VoxCeleb, which is overwhelmingly English, so that assumption has never been
checked. This script checks it, either against a folder of audio files or
against real enrollment_samples rows — see docs/PROJECT_BRIEF.md, open
question 1, and docs/adr/0012-three-passage-bilingual-enrollment.md.

Run with:
    uv run --project backend python scripts/speaker_separation_test.py --audio-dir DIR
    uv run --project backend python scripts/speaker_separation_test.py --from-db
    uv run --project backend python scripts/speaker_separation_test.py --selftest

--audio-dir expects files named <speaker>_<language>[_<take>].wav (or .flac),
e.g. alice_en.wav, alice_en_2.wav, alice_ur.wav, bob_mixed.wav — <language> is
one of en/ur/mixed. The /ml service must be running (ML_SERVICE_URL) since
this mode needs real embeddings extracted from real audio.

--from-db reads accepted enrollment_samples.embedding directly — no /ml call,
works even with the service stopped.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless — this runs from a terminal, not a notebook
import matplotlib.pyplot as plt

from app.core import ml_client
from app.core.db import SessionLocal
from app.models.enrollment_sample import EnrollmentSample
from app.models.user import User

COHORTS = [
    "same_speaker_same_language",
    "same_speaker_cross_language",
    "diff_speaker_same_language",
    "diff_speaker_cross_language",
]

# Speaker names may contain underscores; language is anchored to the three
# known enrollment languages so the split is unambiguous either way.
FILENAME_RE = re.compile(r"^(?P<speaker>.+)_(?P<language>en|ur|mixed)(?:_(?P<take>\d+))?$")


@dataclass(frozen=True)
class Sample:
    speaker: str
    language: str
    embedding: list[float]


def load_from_audio_dir(directory: Path) -> list[Sample]:
    samples: list[Sample] = []
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in (".wav", ".flac"))
    for path in paths:
        match = FILENAME_RE.match(path.stem)
        if not match:
            print(f"  skip (name isn't <speaker>_<language>[_<take>]): {path.name}")
            continue
        result = ml_client.embed_sample(path.read_bytes())
        if not result.accepted:
            print(f"  skip (quality gate: {result.reason_code}): {path.name}")
            continue
        samples.append(
            Sample(speaker=match.group("speaker"), language=match.group("language"), embedding=result.embedding)
        )
    return samples


def load_from_db() -> list[Sample]:
    db = SessionLocal()
    try:
        rows = db.query(EnrollmentSample, User.display_name).join(
            User, User.id == EnrollmentSample.user_id
        ).filter(EnrollmentSample.accepted.is_(True)).all()
    finally:
        db.close()
    # display_name, not user_id, purely so the printed table is legible —
    # nothing here is exported or stored, so this isn't a privacy call.
    return [
        Sample(speaker=display_name, language=sample.language.value, embedding=[float(x) for x in sample.embedding])
        for sample, display_name in rows
    ]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def classify_pair(a: Sample, b: Sample) -> str:
    same_speaker = a.speaker == b.speaker
    same_language = a.language == b.language
    if same_speaker:
        return "same_speaker_same_language" if same_language else "same_speaker_cross_language"
    return "diff_speaker_same_language" if same_language else "diff_speaker_cross_language"


def compute_pairs(samples: list[Sample]) -> dict[str, list[float]]:
    cohorts: dict[str, list[float]] = {name: [] for name in COHORTS}
    for a, b in combinations(samples, 2):
        cohorts[classify_pair(a, b)].append(cosine_similarity(a.embedding, b.embedding))
    return cohorts


def compute_eer(genuine: list[float], impostor: list[float]) -> float | None:
    """Equal error rate: the point where the false-accept rate (impostor pairs
    scoring above threshold) and false-reject rate (genuine pairs scoring
    below it) cross. Swept over every observed score rather than a fixed grid
    — exact for the sample sizes this script will ever see."""
    if not genuine or not impostor:
        return None
    thresholds = sorted(set(genuine) | set(impostor))
    best_gap, eer = None, None
    for t in thresholds:
        far = sum(1 for s in impostor if s >= t) / len(impostor)
        frr = sum(1 for s in genuine if s < t) / len(genuine)
        gap = abs(far - frr)
        if best_gap is None or gap < best_gap:
            best_gap, eer = gap, (far + frr) / 2
    return eer


def print_table(cohorts: dict[str, list[float]]) -> None:
    print(f"{'cohort':<32}{'n pairs':>9}{'mean cos-sim':>15}{'std':>9}")
    for name in COHORTS:
        scores = cohorts[name]
        if not scores:
            note = "unavailable" if name == "same_speaker_same_language" else "0"
            print(f"{name:<32}{'0':>9}{note:>15}{'':>9}")
            continue
        mean = sum(scores) / len(scores)
        std = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))
        print(f"{name:<32}{len(scores):>9}{mean:>15.3f}{std:>9.3f}")


def save_histogram(genuine: list[float], impostor: list[float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.hist(genuine, bins=20, alpha=0.6, label=f"same speaker (n={len(genuine)})", color="#14B8A6")
    plt.hist(impostor, bins=20, alpha=0.6, label=f"different speaker (n={len(impostor)})", color="#EF4444")
    plt.xlabel("cosine similarity")
    plt.ylabel("pair count")
    plt.title("ECAPA-TDNN speaker separation — genuine vs impostor pairs")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _eer_line(label: str, eer: float | None, hint: str = "insufficient data") -> str:
    return f"Equal error rate ({label}): {f'{eer:.1%}' if eer is not None else hint}"


def run(samples: list[Sample], output_path: Path) -> None:
    if len(samples) < 2:
        print(f"Only {len(samples)} usable sample(s) — need at least 2 to compare anything.")
        return

    n_speakers = len({s.speaker for s in samples})
    n_languages = len({s.language for s in samples})
    print(f"\nLoaded {len(samples)} samples — {n_speakers} speaker(s), {n_languages} language(s).\n")

    cohorts = compute_pairs(samples)
    print_table(cohorts)

    genuine_all = cohorts["same_speaker_same_language"] + cohorts["same_speaker_cross_language"]
    impostor_all = cohorts["diff_speaker_same_language"] + cohorts["diff_speaker_cross_language"]

    print()
    print(_eer_line("overall", compute_eer(genuine_all, impostor_all)))
    print(
        _eer_line(
            "within-language",
            compute_eer(cohorts["same_speaker_same_language"], cohorts["diff_speaker_same_language"]),
            hint="insufficient data (needs 2+ takes of the same passage from one speaker)",
        )
    )
    print(_eer_line("cross-language", compute_eer(cohorts["same_speaker_cross_language"], cohorts["diff_speaker_cross_language"])))

    # The number that actually matters — see the module docstring.
    cross_lang_genuine = cohorts["same_speaker_cross_language"]
    if cross_lang_genuine and impostor_all:
        genuine_mean = sum(cross_lang_genuine) / len(cross_lang_genuine)
        impostor_mean = sum(impostor_all) / len(impostor_all)
        print(f"\nSame-speaker cross-language mean ({genuine_mean:.3f}) vs cross-speaker mean ({impostor_mean:.3f}): "
              f"gap {genuine_mean - impostor_mean:+.3f}")
        if genuine_mean - impostor_mean < 0.1:
            print("Gap is small — the 0.75 threshold may not transfer across languages. See ADR-0012.")

    if genuine_all and impostor_all:
        save_histogram(genuine_all, impostor_all, output_path)
        print(f"\nHistogram saved to {output_path}")


def _selftest() -> None:
    """Plain asserts, not pytest — this script lives in /scripts, one level
    removed from the backend package pytest already covers. Run with
    --selftest; exits non-zero (via AssertionError) on failure."""
    m = FILENAME_RE.match("ali_raza_en_2")
    assert m and m.group("speaker") == "ali_raza" and m.group("language") == "en" and m.group("take") == "2"
    m = FILENAME_RE.match("bob_ur")
    assert m and m.group("speaker") == "bob" and m.group("language") == "ur" and m.group("take") is None
    assert FILENAME_RE.match("nonsense") is None

    a_en = Sample("alice", "en", [1.0, 0.0])
    a_ur = Sample("alice", "ur", [0.0, 1.0])
    b_en = Sample("bob", "en", [1.0, 0.0])
    b_ur = Sample("bob", "ur", [-1.0, 0.0])
    assert classify_pair(a_en, a_ur) == "same_speaker_cross_language"
    assert classify_pair(a_en, b_en) == "diff_speaker_same_language"
    assert classify_pair(a_ur, b_ur) == "diff_speaker_same_language"  # both "ur", different speakers
    assert classify_pair(a_en, b_ur) == "diff_speaker_cross_language"

    assert math.isclose(cosine_similarity([1, 0], [1, 0]), 1.0)
    assert math.isclose(cosine_similarity([1, 0], [0, 1]), 0.0)
    assert cosine_similarity([0, 0], [1, 0]) == 0.0  # no divide-by-zero

    clean = compute_eer([0.95, 0.97, 0.96], [0.05, 0.10, 0.02])
    assert clean is not None and clean < 0.05  # near-perfect separation -> near-zero EER

    coin_flip = compute_eer([0.5, 0.5], [0.5, 0.5])
    assert coin_flip is not None and math.isclose(coin_flip, 0.5, abs_tol=0.01)  # total overlap -> ~50%

    assert compute_eer([], [0.5]) is None  # missing either side -> no verdict, not a crash

    print("selftest OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--audio-dir", type=Path, help="Directory of <speaker>_<language>[_<take>].wav/.flac files")
    source.add_argument("--from-db", action="store_true", help="Read accepted enrollment_samples embeddings")
    parser.add_argument("--selftest", action="store_true", help="Run the built-in self-check and exit")
    parser.add_argument("--output", type=Path, default=Path("scripts/speaker_separation_report.png"))
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return

    if not args.audio_dir and not args.from_db:
        parser.error("one of --audio-dir or --from-db is required (or pass --selftest)")

    samples = load_from_db() if args.from_db else load_from_audio_dir(args.audio_dir)
    run(samples, args.output)


if __name__ == "__main__":
    sys.exit(main())
