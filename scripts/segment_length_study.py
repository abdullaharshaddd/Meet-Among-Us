"""Does segment length explain why short clips score low against a voiceprint?

Part 1 checks the /embed and /segments code paths give the same embedding for the same
audio. Part 2 cuts every enrollment recording into windows of several lengths and scores
each window against every voiceprint. A user's own voiceprint is rebuilt without the
recording being tested (leave-one-out), so audio is never scored against itself.

Needs the recordings first:
    cd backend && PYTHONPATH=. uv run python ../scripts/export_enrollment_audio.py DATA_DIR

Then, from the ML environment:
    cd ml && uv run --with matplotlib python ../scripts/segment_length_study.py DATA_DIR

Writes docs/evaluation/segment_length.md and docs/evaluation/segment_length.png.
"""

import argparse
import json
import statistics
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml import audio, embedding, segments, vad

WINDOW_LENGTHS = [1.5, 2.0, 3.0, 4.0, 6.0]
EVALUATION_DIR = Path(__file__).resolve().parent.parent / "docs" / "evaluation"


@dataclass
class Sample:
    user: str
    language: str
    samples: np.ndarray
    full_embedding: list[float]
    stored_embedding: list[float]


def cosine(a: list[float], b: list[float]) -> float:
    return float(np.dot(embedding.normalise(a), embedding.normalise(b)))


def build_centroid(embeddings: list[list[float]]) -> list[float]:
    unit_vectors = [embedding.normalise(vector) for vector in embeddings]

    return embedding.normalise(list(np.mean(unit_vectors, axis=0)))


def load_samples(data_dir: Path) -> list[Sample]:
    loaded = []

    for entry in json.loads((data_dir / "manifest.json").read_text()):
        raw_samples, sample_rate = audio.decode((data_dir / entry["file"]).read_bytes())
        samples = audio.normalise_amplitude(raw_samples)
        loaded.append(
            Sample(
                user=entry["user"],
                language=entry["language"],
                samples=samples,
                full_embedding=embedding.embed(samples),
                stored_embedding=entry["stored_embedding"],
            )
        )

    return loaded


def check_pipeline_parity(loaded: list[Sample]) -> list[str]:
    """/embed embeds the whole normalised clip. /segments embeds VAD regions of the same
    normalised clip. With merging and splitting forced open, /segments should produce one
    region, and its embedding should match /embed's closely."""
    rows = ["| Sample | /embed vs /segments (splitting off) | /embed vs stored in DB |", "|---|---|---|"]
    one_big_segment = segments.SegmentSettings(
        merge_gap_sec=1e9, min_segment_sec=1.0, split_over_sec=1e9, window_sec=4.0, absorb_under_sec=2.0
    )

    for sample in loaded:
        found = segments.find_segments(sample.samples, audio.TARGET_SAMPLE_RATE, one_big_segment)
        versus_segments = cosine(sample.full_embedding, found[0].embedding)
        versus_stored = cosine(sample.full_embedding, sample.stored_embedding)
        rows.append(f"| {sample.user} {sample.language} | {versus_segments:.4f} | {versus_stored:.4f} |")

    return rows


def cut_windows(sample: Sample, length: float, merge_gap_sec: float) -> list[np.ndarray]:
    sample_rate = audio.TARGET_SAMPLE_RATE
    intervals = segments.merge_close_intervals(
        vad.detect_speech_intervals(sample.samples, sample_rate), merge_gap_sec
    )
    windows = []

    for start, end in intervals:
        window_start = start

        while window_start + length <= end:
            windows.append(sample.samples[int(window_start * sample_rate) : int((window_start + length) * sample_rate)])
            window_start += length

    return windows


def score_windows(loaded: list[Sample], embeddings_for: dict[int, list[list[float]]]) -> dict:
    """Returns, for one window length, every same-speaker score, every different-speaker
    score, and one (correct, margin) pair per window."""
    users = sorted({sample.user for sample in loaded})
    full_centroids = {
        user: build_centroid([s.full_embedding for s in loaded if s.user == user]) for user in users
    }
    same, different, outcomes = [], [], []
    enrolled_records, outsider_records, window_scores = [], [], []
    per_user_same: dict[str, list[float]] = {user: [] for user in users}

    for index, sample in enumerate(loaded):
        others_of_user = [s.full_embedding for i, s in enumerate(loaded) if s.user == sample.user and i != index]
        scored_centroids = dict(full_centroids)
        scored_centroids[sample.user] = build_centroid(others_of_user)

        for vector in embeddings_for[index]:
            scores = {user: cosine(vector, centroid) for user, centroid in scored_centroids.items()}
            ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

            window_scores.append((sample.user, scores))
            same.append(scores[sample.user])
            per_user_same[sample.user].append(scores[sample.user])
            different.extend(score for user, score in scores.items() if user != sample.user)
            outcomes.append((ranked[0][0] == sample.user, ranked[0][1] - ranked[1][1]))
            enrolled_records.append((ranked[0][0] == sample.user, ranked[0][1], ranked[0][1] - ranked[1][1]))

            # Same window again, but as if this person had never enrolled: whoever the
            # best match is, naming them would be a wrong name.
            outsider_ranked = [item for item in ranked if item[0] != sample.user]
            outsider_records.append((outsider_ranked[0][1], outsider_ranked[0][1] - outsider_ranked[1][1]))

    return {
        "same": same,
        "different": different,
        "outcomes": outcomes,
        "per_user_same": per_user_same,
        "enrolled_records": enrolled_records,
        "outsider_records": outsider_records,
        "window_scores": window_scores,
    }


FLOORS = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
MARGINS = [0.0, 0.05, 0.10]


def rule_outcomes(result: dict, floor: float, margin: float) -> dict:
    enrolled, outsiders = result["enrolled_records"], result["outsider_records"]
    named_right = sum(correct and best >= floor and gap >= margin for correct, best, gap in enrolled)
    named_wrong = sum((not correct) and best >= floor and gap >= margin for correct, best, gap in enrolled)
    outsider_named = sum(best >= floor and gap >= margin for best, gap in outsiders)

    return {
        "right": named_right / len(enrolled),
        "wrong": named_wrong / len(enrolled),
        "outsider": outsider_named / len(outsiders),
    }


def best_rule(result: dict) -> tuple[float, float, dict]:
    """The rule that names the most enrolled windows correctly while keeping wrong names
    among enrolled speakers at or under 2% and outsiders named at or under 5%."""
    best = (0.75, 0.0, rule_outcomes(result, 0.75, 0.0))

    for floor in FLOORS:
        for margin in MARGINS:
            outcome = rule_outcomes(result, floor, margin)

            if outcome["wrong"] <= 0.02 and outcome["outsider"] <= 0.05 and outcome["right"] > best[2]["right"]:
                best = (floor, margin, outcome)

    return best


def summarise(result: dict) -> dict:
    same, different, outcomes = result["same"], result["different"], result["outcomes"]

    floor, margin, outcome = best_rule(result)

    return {
        "best_floor": floor,
        "best_margin": margin,
        "best_outcome": outcome,
        "result": result,
        "windows": len(outcomes),
        "same_mean": statistics.mean(same),
        "same_min": min(same),
        "same_over_075": sum(score >= 0.75 for score in same) / len(same),
        "diff_mean": statistics.mean(different),
        "diff_max": max(different),
        "top1": sum(correct for correct, _ in outcomes) / len(outcomes),
        "median_margin": statistics.median(margin for _, margin in outcomes),
        "per_user": {user: statistics.mean(scores) for user, scores in result["per_user_same"].items() if scores},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--exclude-pair", help="two display names, e.g. mubashra,Vaniya")
    parser.add_argument(
        "--params-json",
        default='{"merge_gap_sec": 0.3, "floor_base": 0.55, "floor_slope": 0.05, "floor_cap": 0.72}',
        help="floor parameters to evaluate; the rerun script passes the backend's current values",
    )
    arguments = parser.parse_args()

    parameters = json.loads(arguments.params_json)
    embedding.load_model()
    loaded = load_samples(arguments.data_dir)
    parity_rows = check_pipeline_parity(loaded)

    summaries = {}

    pair_rows = ["| Window | Pair type | Pairs | Mean | 5th percentile | 95th percentile | Max |", "|---|---|---|---|---|---|---|"]

    for length in WINDOW_LENGTHS:
        embeddings_for = {
            index: [embedding.embed(window) for window in cut_windows(sample, length, parameters["merge_gap_sec"])]
            for index, sample in enumerate(loaded)
        }
        summaries[str(length)] = summarise(score_windows(loaded, embeddings_for))
        pair_rows += window_pair_rows(loaded, embeddings_for, length)
        print(f"{length}s done")

    full_embeddings = {index: [sample.full_embedding] for index, sample in enumerate(loaded)}
    summaries["full clip"] = summarise(score_windows(loaded, full_embeddings))

    smoothing = {}
    three_second = {
        index: [embedding.embed(window) for window in cut_windows(sample, 3.0, parameters["merge_gap_sec"])]
        for index, sample in enumerate(loaded)
    }

    for run_length in [1, 2, 3, 4]:
        smoothed = {index: average_runs(vectors, run_length) for index, vectors in three_second.items()}
        smoothing[run_length] = summarise(score_windows(loaded, smoothed))

    excluded_pair = tuple(arguments.exclude_pair.split(",")) if arguments.exclude_pair else None

    write_report(parity_rows, summaries, loaded, smoothing, pair_rows, excluded_pair, parameters)
    write_plot(summaries)


def window_pair_rows(loaded: list[Sample], embeddings_for: dict[int, list[list[float]]], length: float) -> list[str]:
    """Window-to-window similarity, the quantity the unknown-speaker grouping threshold is
    applied to. Pairs inside one recording are the case grouping meets in a real clip."""
    pairs: dict[str, list[float]] = {"same person, same recording": [], "same person, other recording": [], "different people": []}

    for i, first in enumerate(loaded):
        for j, second in enumerate(loaded):
            if j < i:
                continue

            for a_index, a in enumerate(embeddings_for[i]):
                for b_index, b in enumerate(embeddings_for[j]):
                    if i == j and b_index <= a_index:
                        continue

                    if i == j:
                        kind = "same person, same recording"
                    elif first.user == second.user:
                        kind = "same person, other recording"
                    else:
                        kind = "different people"

                    pairs[kind].append(cosine(a, b))

    rows = []

    for kind, scores in pairs.items():
        if scores:
            low, high = np.percentile(scores, [5, 95])
            rows.append(f"| {length} s | {kind} | {len(scores)} | {np.mean(scores):.3f} | {low:.3f} | {high:.3f} | {max(scores):.3f} |")

    return rows


def floor_for(seconds: float, parameters: dict) -> float:
    return min(parameters["floor_base"] + parameters["floor_slope"] * seconds, parameters["floor_cap"])


def pair_score_rows(summaries: dict) -> list[str]:
    """Highest and mean score between each pair of different people, per window length. A
    pair that stands out probably shares a device, not a voice."""
    rows = ["| Window | Pair | Windows | Mean | Max |", "|---|---|---|---|---|"]

    for name, summary in summaries.items():
        by_pair: dict[tuple[str, str], list[float]] = {}

        for user, scores in summary["result"]["window_scores"]:
            for other, score in scores.items():
                if other != user:
                    by_pair.setdefault(tuple(sorted((user, other))), []).append(score)

        for pair, scores in sorted(by_pair.items()):
            rows.append(f"| {name} | {pair[0]} / {pair[1]} | {len(scores)} | {np.mean(scores):.3f} | {max(scores):.3f} |")

    return rows


def outsider_rows(summaries: dict, excluded_pair: tuple[str, str] | None, parameters: dict) -> list[str]:
    """Pretend each window's speaker never enrolled. Whoever scores highest among the others
    would wrongly be named if it passed the floor. Run once with every other person counted
    and once with the excluded pair never compared against each other."""
    rows = [
        "| Window | Floor | Outsider max, all pairs | Named at floor, all pairs | Outsider max, pair excluded | Named at floor, pair excluded |",
        "|---|---|---|---|---|---|",
    ]

    for name, summary in summaries.items():
        seconds = float(name) if name != "full clip" else 99.0
        floor = floor_for(seconds, parameters)
        everyone, without_pair = [], []

        for user, scores in summary["result"]["window_scores"]:
            others = {other: score for other, score in scores.items() if other != user}
            everyone.append(max(others.values()))
            kept = [
                score for other, score in others.items()
                if excluded_pair is None or {user, other} != set(excluded_pair)
            ]

            if kept:
                without_pair.append(max(kept))

        cells = [
            f"{max(values):.3f} | {sum(v >= floor for v in values) / len(values):.0%}" if values else "n/a | n/a"
            for values in (everyone, without_pair)
        ]
        rows.append(f"| {name} | {floor:.3f} | {cells[0]} | {cells[1]} |")

    return rows


def average_runs(vectors: list[list[float]], run_length: int) -> list[list[float]]:
    """Averages each run of neighbouring embeddings into one, as if the segments of one
    turn had been pooled before the decision."""
    runs = [vectors[i : i + run_length] for i in range(0, len(vectors), run_length)]

    return [build_centroid(run) for run in runs if len(run) == run_length]


def grid_rows(summary: dict) -> list[str]:
    rows = ["| Floor | " + " | ".join(f"margin {m:.2f}" for m in MARGINS) + " |", "|---" * (len(MARGINS) + 1) + "|"]

    for floor in FLOORS:
        cells = []

        for margin in MARGINS:
            outcome = rule_outcomes(summary["result"], floor, margin)
            cells.append(f"{outcome['right']:.0%} / {outcome['wrong']:.0%} / {outcome['outsider']:.0%}")

        rows.append(f"| {floor:.2f} | " + " | ".join(cells) + " |")

    return rows


def write_report(
    parity_rows: list[str],
    summaries: dict,
    loaded: list[Sample],
    smoothing: dict,
    pair_rows: list[str],
    excluded_pair: tuple[str, str] | None,
    parameters: dict,
) -> None:
    users = sorted({sample.user for sample in loaded})
    lines = [
        "# Segment length study",
        "",
        f"{len(loaded)} enrollment recordings ({len(users)} users x 3 languages). Windows are cut from VAD speech only,",
        "non-overlapping, and every window is scored against all voiceprints. A user's own voiceprint is",
        "rebuilt without the recording being tested (leave-one-out), so it is built from only 2 recordings;",
        "other users' voiceprints are the stored full ones.",
        "",
        "## Pipeline parity",
        "",
        "Same decode and amplitude normalisation in both endpoints; table shows the embeddings agree.",
        "",
        *parity_rows,
        "",
        "## Scores by window length",
        "",
        "| Window | Windows | Same mean | Same min | Same >= 0.75 | Diff mean | Diff max | Top-1 correct | Median margin |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for name, summary in summaries.items():
        label = f"{name} s" if name != "full clip" else name
        lines.append(
            f"| {label} | {summary['windows']} | {summary['same_mean']:.3f} | {summary['same_min']:.3f} | "
            f"{summary['same_over_075']:.0%} | {summary['diff_mean']:.3f} | {summary['diff_max']:.3f} | "
            f"{summary['top1']:.0%} | {summary['median_margin']:.3f} |"
        )

    lines += ["", "## Mean same-speaker score per user", "", "| Window | " + " | ".join(users) + " |", "|---" * (len(users) + 1) + "|"]

    for name, summary in summaries.items():
        cells = " | ".join(f"{summary['per_user'].get(user, float('nan')):.3f}" for user in users)
        lines.append(f"| {name} | {cells} |")

    lines += [
        "",
        "## Best decision rule per window length",
        "",
        "Rule: name the best match only if best >= floor and (best - runner-up) >= margin, else Unknown.",
        "Chosen as the rule naming the most windows correctly while naming a wrong enrolled person in at",
        "most 2% of windows and naming an outsider (someone not enrolled) in at most 5%.",
        "",
        "| Window | Floor | Margin | Named correctly | Named wrongly | Outsider named |",
        "|---|---|---|---|---|---|",
    ]

    for name, summary in summaries.items():
        outcome = summary["best_outcome"]
        lines.append(
            f"| {name} | {summary['best_floor']:.2f} | {summary['best_margin']:.2f} | "
            f"{outcome['right']:.0%} | {outcome['wrong']:.0%} | {outcome['outsider']:.0%} |"
        )

    lines += ["", "## Full rule grids", "", "Each cell: named correctly / named wrongly (enrolled) / outsider named."]

    for name, summary in summaries.items():
        lines += ["", f"### {name}", "", *grid_rows(summary)]

    lines += [
        "",
        "## Smoothing: average neighbouring 3 s windows before deciding",
        "",
        "| Windows pooled | Pooled length | Decisions | Same mean | Same min | Diff max | Top-1 | Best floor | Best margin | Named correctly | Named wrongly | Outsider named |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for run_length, summary in smoothing.items():
        outcome = summary["best_outcome"]
        lines.append(
            f"| {run_length} | {3 * run_length} s | {summary['windows']} | {summary['same_mean']:.3f} | "
            f"{summary['same_min']:.3f} | {summary['diff_max']:.3f} | {summary['top1']:.0%} | "
            f"{summary['best_floor']:.2f} | {summary['best_margin']:.2f} | {outcome['right']:.0%} | "
            f"{outcome['wrong']:.0%} | {outcome['outsider']:.0%} |"
        )

    lines += ["", "## Window-to-window similarity (for the unknown-speaker grouping threshold)", "", *pair_rows]

    lines += [
        "",
        "## Score between each pair of different people",
        "",
        "A pair far above the others probably shares a device, so its score reflects the recording",
        "setup as much as the voices.",
        "",
        *pair_score_rows(summaries),
        "",
        "## Outsider check against the current floor",
        "",
        f"Floor = min({parameters['floor_base']} + {parameters['floor_slope']} x seconds, {parameters['floor_cap']}).",
        "Excluded pair: " + (" / ".join(excluded_pair) if excluded_pair else "none given"),
        "",
        *outsider_rows(summaries, excluded_pair, parameters),
    ]

    lines += [
        "",
        "## Caveats",
        "",
        "- The recordings come from different devices (webm for one user, wav for the others). A device",
        "  mismatch lowers scores, and a user's three recordings share a device, which flatters same-speaker",
        "  scores relative to a clip recorded on a different phone.",
        "- Leave-one-out voiceprints use 2 recordings in 2 other languages, so same-speaker scores here are",
        "  more pessimistic than production, where the voiceprint is built from all 3.",
        "- Only 3 users, so the differing-speaker numbers are 2 impostors per window.",
    ]

    (EVALUATION_DIR / "segment_length.md").write_text("\n".join(lines) + "\n")


def write_plot(summaries: dict) -> None:
    names = list(summaries)
    positions = range(len(names))
    figure, axis = plt.subplots(figsize=(8, 5))

    axis.plot(positions, [summaries[n]["same_mean"] for n in names], marker="o", label="same speaker, mean")
    axis.plot(positions, [summaries[n]["same_min"] for n in names], marker="o", linestyle=":", label="same speaker, min")
    axis.plot(positions, [summaries[n]["diff_mean"] for n in names], marker="s", label="different speaker, mean")
    axis.plot(positions, [summaries[n]["diff_max"] for n in names], marker="s", linestyle=":", label="different speaker, max")
    axis.axhline(0.75, color="grey", linestyle="--", linewidth=1, label="current threshold 0.75")
    axis.set_xticks(list(positions))
    axis.set_xticklabels([f"{n} s" if n != "full clip" else n for n in names])
    axis.set_xlabel("window length")
    axis.set_ylabel("cosine similarity")
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(EVALUATION_DIR / "segment_length.png", dpi=150)


if __name__ == "__main__":
    main()
