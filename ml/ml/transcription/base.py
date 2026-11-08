"""Shared shapes and rules for every transcription engine."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Protocol

import requests

RETRY_DELAYS_SEC = (1.0, 2.0, 4.0)
DEVANAGARI = re.compile("[ऀ-ॿ]")

# Urdu in Urdu script with English work words left in English letters, so Whisper does not
# drift into Hindi/Devanagari or turn English words into Urdu spelling.
URDU_PROMPT = (
    "یہ ایک عام گفتگو ہے۔ ہم project، deadline، client اور meeting کے بارے میں بات کر رہے ہیں، "
    "اور کبھی اردو اور English ملا کر بولتے ہیں۔"
)

# Replaced in tests so a retry does not really sleep.
sleep = time.sleep


class TranscriptionError(Exception):
    """Base for everything the service turns into an HTTP error. Messages never carry keys."""

    status_code = 502


class MissingApiKeyError(TranscriptionError):
    status_code = 503

    def __init__(self, variable: str) -> None:
        super().__init__(f"{variable} is not set. Add it to ml/.env and restart the ML service.")


class RateLimitedError(TranscriptionError):
    status_code = 429


class ProviderError(TranscriptionError):
    status_code = 502


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Transcript:
    language: str | None  # as the engine reported it, for the whole file
    words: list[Word]


class Transcriber(Protocol):
    name: str

    def transcribe(self, flac_bytes: bytes, language: str | None) -> Transcript: ...


def post_with_retry(send: Callable[[], requests.Response], provider: str) -> requests.Response:
    """Retries a rate-limited request up to 3 times, waiting longer each time (or as long as
    the provider asks). Any other failure is reported once, without request details."""
    for attempt in range(len(RETRY_DELAYS_SEC) + 1):
        try:
            response = send()
        except requests.RequestException as exc:
            raise ProviderError(f"{provider} could not be reached ({type(exc).__name__}).") from None

        if response.status_code == 429:
            if attempt == len(RETRY_DELAYS_SEC):
                raise RateLimitedError(
                    f"{provider} rate limit still hit after {len(RETRY_DELAYS_SEC)} retries. Wait a minute and try again."
                )

            sleep(_retry_wait(response, RETRY_DELAYS_SEC[attempt]))
            continue

        if not response.ok:
            raise ProviderError(f"{provider} returned {response.status_code}: {response.text[:200]}")

        return response

    raise ProviderError(f"{provider} request failed.")


def _retry_wait(response: requests.Response, default: float) -> float:
    try:
        return min(float(response.headers.get("retry-after", default)), 30.0)
    except ValueError:
        return default


def script_warning(words: list[Word]) -> str | None:
    """Whisper sometimes writes Urdu speech in Devanagari (Hindi script). Flag it rather than
    passing it on silently."""
    hits = [word.text for word in words if DEVANAGARI.search(word.text)]

    if not hits:
        return None

    return f"{len(hits)} word(s) came back in Devanagari instead of Urdu script, for example {hits[0]!r}."
