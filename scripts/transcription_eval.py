"""How accurate are the transcription engines on our clips?

Give it a folder of clips, each with a hand-written reference transcript beside it
(clip1.m4a + clip1.txt). It runs every clip through each engine via the ML service and reports
word error rate (WER) and character error rate (CER) per clip and overall. CER matters more for
Urdu, because where one word ends and the next begins is written inconsistently. It also prints
the speaker-separation numbers, so one report answers both "are the words right" and "does
the matching threshold make sense".

References must be written by a person listening to the audio. Do not use machine captions
(for example a video call's caption track) as references.

Run with (ML service running with its keys):
    cd backend && PYTHONPATH=. uv run python ../scripts/transcription_eval.py CLIPS_DIR
    cd backend && PYTHONPATH=. uv run python ../scripts/transcription_eval.py --selftest

Writes docs/evaluation/transcription_results.md.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests

AUDIO_SUFFIXES = {".m4a", ".webm", ".wav", ".flac"}
RESULTS_FILE = Path(__file__).resolve().parent.parent / "docs" / "evaluation" / "transcription_results.md"

# Arabic-script letters that look alike and are used interchangeably in Urdu text. Everything
# on the left is rewritten to the Urdu form on the right before scoring.
SIMILAR_LETTERS = {
    "ي": "ی",  # Arabic yeh -> Farsi/Urdu yeh
    "ى": "ی",  # alef maksura -> Urdu yeh
    "ك": "ک",  # Arabic kaf -> Urdu kaf
    "ه": "ہ",  # Arabic heh -> Urdu heh goal
    "ە": "ہ",  # ae -> heh goal
}
# Zabar, zer, pesh, shadda, sukun and their relatives: written inconsistently, so dropped.
DIACRITICS = re.compile("[ً-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ]")
INVISIBLE = re.compile("[​-‏‪-‮⁦-⁩ـ]")  # joiners, direction marks, tatweel
DIGITS = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")} | {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = INVISIBLE.sub("", text)
    text = DIACRITICS.sub("", text)
    text = "".join(SIMILAR_LETTERS.get(character, character) for character in text)
    text = text.translate(DIGITS).lower()
    text = text.replace("'", "").replace("’", "")
    text = "".join(" " if unicodedata.category(character)[0] in "PS" else character for character in text)

    return " ".join(text.split())


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))

    for i, ref_item in enumerate(reference, start=1):
        current = [i]

        for j, hyp_item in enumerate(hypothesis, start=1):
            cost = 0 if ref_item == hyp_item else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))

        previous = current

    return previous[-1]


@dataclass
class Score:
    word_edits: int
    word_total: int
    char_edits: int
    char_total: int

    @property
    def wer(self) -> float:
        return self.word_edits / self.word_total

    @property
    def cer(self) -> float:
        return self.char_edits / self.char_total


def score(reference: str, hypothesis: str) -> Score:
    ref, hyp = normalise(reference), normalise(hypothesis)
    # CER ignores spaces, since Urdu word boundaries are inconsistent.
    ref_chars, hyp_chars = list(ref.replace(" ", "")), list(hyp.replace(" ", ""))

    return Score(
        word_edits=edit_distance(ref.split(), hyp.split()),
        word_total=len(ref.split()),
        char_edits=edit_distance(ref_chars, hyp_chars),
        char_total=len(ref_chars),
    )


@dataclass
class Run:
    clip: str
    engine: str
    seconds: float
    score: Score | None
    script_warning: str | None
    error: str | None


def transcribe_clip(path: Path, engine: str, ml_url: str, language: str) -> tuple[str | None, float, str | None, str | None]:
    started = time.perf_counter()

    try:
        response = requests.post(
            f"{ml_url}/transcribe",
            params={"engine": engine, "language": language},
            data=path.read_bytes(),
            headers={"Content-Type": "application/octet-stream"},
            timeout=900,
        )
    except requests.RequestException as exc:
        return None, time.perf_counter() - started, None, f"ML service unreachable ({type(exc).__name__})"

    elapsed = time.perf_counter() - started

    if not response.ok:
        try:
            detail = response.json()["detail"]
        except (ValueError, KeyError, TypeError):
            detail = f"HTTP {response.status_code}"

        return None, elapsed, None, str(detail)

    body = response.json()

    return " ".join(word["text"] for word in body["words"]), elapsed, body["script_warning"], None


def find_clips(directory: Path) -> list[tuple[Path, str]]:
    clips = []

    for audio in sorted(directory.iterdir()):
        reference = audio.with_suffix(".txt")

        if audio.suffix.lower() in AUDIO_SUFFIXES and reference.exists():
            clips.append((audio, reference.read_text(encoding="utf-8")))

    return clips


def evaluate(directory: Path, engines: list[str], ml_url: str, language: str) -> list[Run]:
    runs = []

    for audio, reference in find_clips(directory):
        if not normalise(reference):
            print(f"skipping {audio.name}: its reference is empty", file=sys.stderr)
            continue

        for engine in engines:
            hypothesis, seconds, warning, error = transcribe_clip(audio, engine, ml_url, language)
            clip_score = score(reference, hypothesis) if hypothesis is not None else None
            runs.append(Run(audio.name, engine, seconds, clip_score, warning, error))
            print(f"{audio.name} [{engine}]: " + (error if error else f"WER {clip_score.wer:.1%}  CER {clip_score.cer:.1%}"))

    return runs


def overall(runs: list[Run], engine: str) -> Score | None:
    scored = [run.score for run in runs if run.engine == engine and run.score]

    if not scored:
        return None

    return Score(
        word_edits=sum(s.word_edits for s in scored),
        word_total=sum(s.word_total for s in scored),
        char_edits=sum(s.char_edits for s in scored),
        char_total=sum(s.char_total for s in scored),
    )


def separation_lines() -> list[str]:
    """Average same-speaker and different-speaker similarity from the stored enrollment
    embeddings, with a plain reading of the 0.75 match threshold."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    try:
        import speaker_separation_test as separation

        cohorts = separation.compute_pairs(separation.load_from_db())
    except Exception as exc:  # noqa: BLE001 - a missing database must not hide the transcription results
        return [f"Speaker separation numbers unavailable: {type(exc).__name__}: {exc}"]

    same = [value for name, values in cohorts.items() if name.startswith("same_speaker") for value in values]
    different = [value for name, values in cohorts.items() if name.startswith("diff_speaker") for value in values]

    if not same or not different:
        return ["Speaker separation numbers unavailable: need at least two people with accepted samples."]

    same_mean, different_mean = statistics.mean(same), statistics.mean(different)
    midpoint = (same_mean + different_mean) / 2
    lines = [
        f"Average same-speaker similarity: {same_mean:.3f} ({len(same)} pairs)",
        f"Average different-speaker similarity: {different_mean:.3f} ({len(different)} pairs)",
        f"Gap: {same_mean - different_mean:.3f}. Highest different-speaker pair: {max(different):.3f}. Lowest same-speaker pair: {min(same):.3f}.",
        "",
    ]

    if same_mean < 0.75:
        lines.append(
            f"0.75 does NOT look sensible as a flat per-clip threshold on this data: it is above the average "
            f"same-speaker score ({same_mean:.2f}), so it would reject the right person often."
        )
    elif max(different) >= 0.75:
        lines.append(
            "0.75 is below the average same-speaker score, but at least one different-speaker pair reaches it, "
            "so it would sometimes name the wrong person."
        )
    else:
        lines.append(
            f"0.75 sits between the averages ({different_mean:.2f} and {same_mean:.2f}), so on whole-clip "
            "embeddings it looks sensible."
        )

    lines.append(
        "These pairs are whole 12 to 25 second enrollment recordings, mostly from one device per person. "
        "Live matching no longer uses a flat 0.75: it uses a floor that rises with seconds of speech (ADR-0020)."
    )

    return lines


def write_report(runs: list[Run], engines: list[str], separation: list[str], output: Path) -> None:
    lines = [
        "# Transcription results",
        "",
        "WER and CER after normalisation: punctuation and Urdu diacritics removed, look-alike Arabic and Urdu",
        "letters unified (ي/ی, ك/ک, ه/ہ), digits unified, English lowercased. CER ignores spaces. References",
        "are hand-written. Spelling variants such as لئے and لیے still count as errors.",
        "",
        "| Clip | Engine | WER | CER | Seconds | Script warning | Error |",
        "|---|---|---|---|---|---|---|",
    ]

    for run in runs:
        wer = f"{run.score.wer:.1%}" if run.score else "n/a"
        cer = f"{run.score.cer:.1%}" if run.score else "n/a"
        lines.append(f"| {run.clip} | {run.engine} | {wer} | {cer} | {run.seconds:.1f} | {run.script_warning or ''} | {run.error or ''} |")

    lines += ["", "## Overall", "", "| Engine | Clips scored | WER | CER |", "|---|---|---|---|"]

    for engine in engines:
        total = overall(runs, engine)
        clips = sum(1 for run in runs if run.engine == engine and run.score)
        lines.append(f"| {engine} | {clips} | " + (f"{total.wer:.1%} | {total.cer:.1%} |" if total else "n/a | n/a |"))

    lines += ["", "Overall rates are total edits divided by total reference length, not an average of clips.", "", "## Speaker separation", "", *separation]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {output}")


def selftest() -> None:
    assert normalise("ہوئی۔") == "ہوئی"
    assert normalise("كيا") == "کیا"
    assert normalise("مَیں") == "میں"
    assert normalise("Hello,  World!") == "hello world"
    assert normalise("don't") == "dont"
    assert normalise("۱۲۳ ٤٥") == "123 45"
    assert edit_distance(list("kitten"), list("sitting")) == 3
    assert edit_distance([], ["a", "b"]) == 2

    same = score("یار deadline قریب ہے۔", "یار Deadline قریب ہے")
    assert (same.word_edits, same.char_edits) == (0, 0)

    wrong = score("a b c d", "a x c")
    assert wrong.word_edits == 2 and wrong.wer == 0.5

    spacing = score("ابھی تک", "ابھیتک")
    assert spacing.char_edits == 0 and spacing.word_edits == 2  # a spacing quirk costs words, not characters
    print("selftest OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("clips", nargs="?", type=Path, help="folder of clip.m4a + clip.txt pairs")
    parser.add_argument("--engines", nargs="+", default=["groq", "elevenlabs"], choices=["groq", "elevenlabs"])
    parser.add_argument("--language", default="ur", choices=["ur", "en", "auto"])
    parser.add_argument("--output", type=Path, default=RESULTS_FILE, help="where to write the report")
    parser.add_argument("--selftest", action="store_true")
    arguments = parser.parse_args()

    if arguments.selftest:
        selftest()
        return

    if arguments.clips is None:
        parser.error("give a clips folder, or pass --selftest")

    from app.core.config import settings

    sys.stdout.reconfigure(encoding="utf-8")
    runs = evaluate(arguments.clips, arguments.engines, settings.ml_service_url, arguments.language)

    if not runs:
        sys.exit("No clip+reference pairs found. Each audio file needs a .txt of the same name beside it.")

    write_report(runs, arguments.engines, separation_lines(), arguments.output)


if __name__ == "__main__":
    main()
