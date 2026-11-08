"""Why did Vaniya's voice on a processed video call look closest to mubashra's voiceprint?

Embeds 4 s windows cut from the call, only from stretches a single person is captioned as
speaking and at least 2 s clear of any caption change, then compares them with enrollment
recordings. Analysis only: nothing in matching is changed.

Needs the enrollment recordings from scripts/export_enrollment_audio.py, plus the call's
audio (FLAC) and caption track (SRT):
    cd ml && uv run python ../scripts/channel_diagnosis.py DATA_DIR CALL.flac CALL.srt

Writes docs/evaluation/channel_diagnosis.md.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np

from ml import audio, embedding, segments, vad

WINDOW_SEC = 4.0
EDGE_CLEARANCE_SEC = 2.0
MERGE_GAP_SEC = 0.3
EVALUATION_FILE = Path(__file__).resolve().parent.parent / "docs" / "evaluation" / "channel_diagnosis.md"


def cosine(a: list[float], b: list[float]) -> float:
    return float(np.dot(embedding.normalise(a), embedding.normalise(b)))


def centroid_of(vectors: list[list[float]]) -> list[float]:
    return embedding.normalise(list(np.mean([embedding.normalise(v) for v in vectors], axis=0)))


def seconds(stamp: str) -> float:
    hours, minutes, rest = stamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest.replace(",", "."))


def single_speaker_stretches(srt_path: Path) -> dict[str, list[tuple[float, float]]]:
    stretches: list[list] = []

    for block in srt_path.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().splitlines()

        if len(lines) < 3 or "-->" not in lines[1]:
            continue

        start, end = (seconds(part.strip()) for part in lines[1].split("-->"))
        names = set(re.findall(r"\(([^)]*)\)", "\n".join(lines[2:])))

        if len(names) != 1:
            stretches.append([start, end, None])
            continue

        name = next(iter(names)).split()[0].lower()

        if stretches and stretches[-1][2] == name and abs(stretches[-1][1] - start) < 0.5:
            stretches[-1][1] = end
        else:
            stretches.append([start, end, name])

    clear: dict[str, list[tuple[float, float]]] = {}

    for start, end, name in stretches:
        if name and end - start > 2 * EDGE_CLEARANCE_SEC:
            clear.setdefault(name, []).append((start + EDGE_CLEARANCE_SEC, end - EDGE_CLEARANCE_SEC))

    return clear


def windows_inside(samples: np.ndarray, speech: list[tuple[float, float]], span: tuple[float, float]) -> list[np.ndarray]:
    rate = audio.TARGET_SAMPLE_RATE
    found = []

    for speech_start, speech_end in speech:
        start, end = max(speech_start, span[0]), min(speech_end, span[1])
        position = start

        while position + WINDOW_SEC <= end:
            found.append(samples[int(position * rate) : int((position + WINDOW_SEC) * rate)])
            position += WINDOW_SEC

    return found


def enrollment_windows(path: Path) -> list[list[float]]:
    raw, _ = audio.decode(path.read_bytes())
    samples = audio.normalise_amplitude(raw)
    speech = segments.merge_close_intervals(vad.detect_speech_intervals(samples, audio.TARGET_SAMPLE_RATE), MERGE_GAP_SEC)
    duration = len(samples) / audio.TARGET_SAMPLE_RATE

    return [embedding.embed(w) for w in windows_inside(samples, speech, (0.0, duration))]


def describe(values: list[float]) -> str:
    low, median, high = np.percentile(values, [5, 50, 95])

    return f"{len(values)} | {np.mean(values):.3f} | {low:.3f} | {median:.3f} | {high:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("call_audio", type=Path)
    parser.add_argument("call_captions", type=Path)
    arguments = parser.parse_args()

    embedding.load_model()
    manifest = json.loads((arguments.data_dir / "manifest.json").read_text())
    people = sorted({entry["user"] for entry in manifest}, key=str.lower)

    enrolment_recordings = {}
    enrolment_window_vectors: dict[str, list[list[float]]] = {person: [] for person in people}
    enrolment_by_recording: dict[str, dict[str, list[float]]] = {person: {} for person in people}

    for entry in manifest:
        raw, _ = audio.decode((arguments.data_dir / entry["file"]).read_bytes())
        samples = audio.normalise_amplitude(raw)
        enrolment_by_recording[entry["user"]][entry["language"]] = embedding.embed(samples)
        enrolment_window_vectors[entry["user"]] += enrollment_windows(arguments.data_dir / entry["file"])

    centroids = {person: centroid_of(list(enrolment_by_recording[person].values())) for person in people}

    raw_call, _ = audio.decode(arguments.call_audio.read_bytes())
    call_samples = audio.normalise_amplitude(raw_call)
    call_speech = segments.merge_close_intervals(
        vad.detect_speech_intervals(call_samples, audio.TARGET_SAMPLE_RATE), MERGE_GAP_SEC
    )
    clear_stretches = single_speaker_stretches(arguments.call_captions)
    call_windows: dict[str, list[list[float]]] = {}

    for name, spans in clear_stretches.items():
        person = next((p for p in people if p.lower() == name), None)

        if person is None:
            continue

        call_windows[person] = [
            embedding.embed(window)
            for span in spans
            for window in windows_inside(call_samples, call_speech, span)
        ]
        print(f"{person}: {len(call_windows[person])} call windows")

    lines = [
        "# Channel diagnosis: call audio versus enrollment recordings",
        "",
        "Analysis only, nothing in matching was changed. 4 s windows were cut from the Google Meet call,",
        "only inside stretches captioned as one speaker and at least 2 s from a caption change (captions",
        "lag, so a window can still straddle a change). Enrollment recordings are the direct recordings",
        "the voiceprints were built from. Columns: windows, mean, 5th percentile, median, 95th percentile.",
        "",
        "## Call window against each person's voiceprint",
        "",
        "| Call speaker | Compared with | Windows | Mean | p5 | Median | p95 |",
        "|---|---|---|---|---|---|---|",
    ]

    for speaker, vectors in call_windows.items():
        for target in people:
            scores = [cosine(vector, centroids[target]) for vector in vectors]
            marker = " (own)" if target == speaker else ""
            lines.append(f"| {speaker} | {target}{marker} voiceprint | {describe(scores)} |")

    lines += [
        "",
        "## Call window against each of the speaker's own enrollment recordings (whole-clip embeddings)",
        "",
        "| Call speaker | Enrollment recording | Windows | Mean | p5 | Median | p95 |",
        "|---|---|---|---|---|---|---|",
    ]

    for speaker, vectors in call_windows.items():
        for language, recording in enrolment_by_recording[speaker].items():
            scores = [cosine(vector, recording) for vector in vectors]
            lines.append(f"| {speaker} | {speaker} {language} | {describe(scores)} |")

    lines += [
        "",
        "## Window against window: call versus enrollment, and enrollment against enrollment",
        "",
        "Same 4 s length on both sides, so length is not the difference. The last row of each group is",
        "the same-condition reference: one person's enrollment windows against their other recordings.",
        "",
        "| Group | Windows pairs | Mean | p5 | Median | p95 |",
        "|---|---|---|---|---|---|",
    ]

    for speaker, vectors in call_windows.items():
        for target in people:
            scores = [cosine(a, b) for a in vectors for b in enrolment_window_vectors[target]]
            marker = " (own)" if target == speaker else ""
            lines.append(f"| call {speaker} vs enrollment {target}{marker} | {describe(scores)} |")

    for person in people:
        pool = enrolment_window_vectors[person]
        scores = [cosine(a, b) for i, a in enumerate(pool) for b in pool[i + 1 :]]
        lines.append(f"| enrollment {person} vs enrollment {person} (reference) | {describe(scores)} |")

    for first_index, first in enumerate(people):
        for second in people[first_index + 1 :]:
            pool_a, pool_b = enrolment_window_vectors[first], enrolment_window_vectors[second]
            scores = [cosine(a, b) for a in pool_a for b in pool_b]
            lines.append(f"| enrollment {first} vs enrollment {second} (reference) | {describe(scores)} |")

    EVALUATION_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {EVALUATION_FILE}")


if __name__ == "__main__":
    main()
