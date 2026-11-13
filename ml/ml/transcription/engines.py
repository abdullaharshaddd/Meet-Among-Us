"""The two transcription engines. Both return the same thing: words with start and end
times, plus the language the engine detected. See docs/adr/0023-transcriber-interface.md.
"""

from __future__ import annotations

import requests

from ml.config import TranscriptionConfig
from ml.transcription.base import (
    URDU_PROMPT,
    MissingApiKeyError,
    ProviderError,
    Transcript,
    Word,
    post_with_retry,
)

TIMEOUT_SEC = 300


class GroqWhisperTranscriber:
    name = "groq"

    def __init__(self, config: TranscriptionConfig) -> None:
        self.config = config

    def transcribe(self, flac_bytes: bytes, language: str | None) -> Transcript:
        if not self.config.groq_api_key:
            raise MissingApiKeyError("GROQ_API_KEY")

        form = {
            "model": self.config.groq_model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }

        if language:
            form["language"] = language

        # The prompt is mixed Urdu and English, so it is also safe when the engine picks the
        # language itself. Only an explicit English request drops it. See ADR-0027.
        if language in ("ur", None):
            form["prompt"] = URDU_PROMPT

        response = post_with_retry(
            lambda: requests.post(
                self.config.groq_api_url,
                headers={"Authorization": f"Bearer {self.config.groq_api_key}"},
                files={"file": ("clip.flac", flac_bytes, "audio/flac")},
                data=form,
                timeout=TIMEOUT_SEC,
            ),
            "Groq",
        )

        return parse_groq(_json_body(response, "Groq"))


class ElevenLabsScribeTranscriber:
    name = "elevenlabs"

    def __init__(self, config: TranscriptionConfig) -> None:
        self.config = config

    def transcribe(self, flac_bytes: bytes, language: str | None) -> Transcript:
        if not self.config.elevenlabs_api_key:
            raise MissingApiKeyError("ELEVENLABS_API_KEY")

        form = {
            "model_id": self.config.elevenlabs_model,
            "timestamps_granularity": "word",
            # Speakers are labelled by our own matching, not by the engine.
            "diarize": "false",
            "tag_audio_events": "false",
        }

        if language:
            form["language_code"] = language

        response = post_with_retry(
            lambda: requests.post(
                self.config.elevenlabs_api_url,
                headers={"xi-api-key": self.config.elevenlabs_api_key},
                files={"file": ("clip.flac", flac_bytes, "audio/flac")},
                data=form,
                timeout=TIMEOUT_SEC,
            ),
            "ElevenLabs",
        )

        return parse_elevenlabs(_json_body(response, "ElevenLabs"))


def _json_body(response: requests.Response, provider: str) -> dict:
    try:
        return response.json()
    except ValueError:
        raise ProviderError(f"{provider} returned something that was not JSON.") from None


def parse_groq(body: dict) -> Transcript:
    # The docs do not show the word entry's field names, so accept both spellings.
    words = [
        Word(text=(item.get("word") or item.get("text") or "").strip(), start=float(item["start"]), end=float(item["end"]))
        for item in body.get("words", [])
    ]

    return Transcript(language=body.get("language"), words=[word for word in words if word.text])


def parse_elevenlabs(body: dict) -> Transcript:
    # `words` also holds spacing and audio-event entries; only real words are kept.
    words = [
        Word(text=item["text"].strip(), start=float(item["start"]), end=float(item["end"]))
        for item in body.get("words", [])
        if item.get("type", "word") == "word" and item.get("text", "").strip()
    ]

    return Transcript(language=body.get("language_code"), words=words)


def build_transcriber(engine: str, config: TranscriptionConfig):
    if engine == "groq":
        return GroqWhisperTranscriber(config)

    return ElevenLabsScribeTranscriber(config)
