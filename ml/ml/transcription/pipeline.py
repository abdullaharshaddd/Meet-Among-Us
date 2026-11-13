"""Turns decoded audio into one word list on one timeline, splitting at silence when the file
is too big for the engine to take in one request."""

from __future__ import annotations

import io

import numpy as np
import soundfile

from ml import vad
from ml.transcription.base import Transcriber, Transcript, Word, script_warning

# Cut points are only searched for in the back half of a chunk, so no chunk comes out tiny.
EARLIEST_CUT_FRACTION = 0.5
# Leave room under the size limit: FLAC size varies with the audio.
SIZE_SAFETY = 0.9


def to_flac(samples: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    soundfile.write(buffer, samples, sample_rate, format="FLAC")

    return buffer.getvalue()


def silence_gaps(speech: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(speech[i][1], speech[i + 1][0]) for i in range(len(speech) - 1)]


def choose_cuts(speech: list[tuple[float, float]], duration: float, max_chunk_sec: float) -> list[float]:
    """Cut at the middle of the longest silence in the back half of each chunk. If there is no
    silence there at all, cut at the limit, which may split a word."""
    gaps = silence_gaps(speech)
    cuts: list[float] = []
    chunk_start = 0.0

    while duration - chunk_start > max_chunk_sec:
        limit = chunk_start + max_chunk_sec
        earliest = chunk_start + max_chunk_sec * EARLIEST_CUT_FRACTION
        candidates = [gap for gap in gaps if earliest <= (gap[0] + gap[1]) / 2 <= limit]

        if candidates:
            start, end = max(candidates, key=lambda gap: gap[1] - gap[0])
            cut = (start + end) / 2
        else:
            cut = limit

        cuts.append(cut)
        chunk_start = cut

    return cuts


def transcribe_samples(
    samples: np.ndarray, sample_rate: int, transcriber: Transcriber, language: str | None, max_bytes: int | None
) -> tuple[Transcript, int]:
    """Returns the merged transcript and how many requests it took."""
    duration = len(samples) / sample_rate
    whole = to_flac(samples, sample_rate)

    if max_bytes is None or len(whole) <= max_bytes:
        return transcriber.transcribe(whole, language), 1

    bytes_per_second = len(whole) / duration
    max_chunk_sec = max_bytes * SIZE_SAFETY / bytes_per_second
    speech = vad.detect_speech_intervals(samples, sample_rate)
    boundaries = [0.0, *choose_cuts(speech, duration, max_chunk_sec), duration]
    words: list[Word] = []
    detected_language = None

    for start, end in zip(boundaries, boundaries[1:]):
        piece = samples[int(start * sample_rate) : int(end * sample_rate)]
        transcript = transcriber.transcribe(to_flac(piece, sample_rate), language)
        detected_language = detected_language or transcript.language
        words += [Word(word.text, word.start + start, word.end + start) for word in transcript.words]

    return Transcript(language=detected_language, words=words), len(boundaries) - 1


def transcribe_auto(
    samples: np.ndarray, sample_rate: int, transcriber: Transcriber, max_bytes: int | None
) -> tuple[Transcript, int]:
    """Lets the engine detect the language, then retries once as Urdu if the words came back in
    Devanagari. Whisper often calls Urdu-English speech "Hindi" and writes Hindi script, which is
    wrong for this product. English and plain Urdu keep their first result. See ADR-0027."""
    transcript, requests_made = transcribe_samples(samples, sample_rate, transcriber, None, max_bytes)

    if script_warning(transcript.words) is None:
        return transcript, requests_made

    retried, more_requests = transcribe_samples(samples, sample_rate, transcriber, "ur", max_bytes)

    return retried, requests_made + more_requests
