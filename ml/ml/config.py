"""Transcription settings, read from the environment (ml/.env, loaded with
`uv run --env-file .env uvicorn ...`).

A missing API key never stops the service from starting, because the same service also
handles enrollment. It is logged as a warning at boot, and /transcribe answers 503
naming the variable when the chosen engine's key is missing.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ENGINES = ("groq", "elevenlabs")


@dataclass(frozen=True)
class TranscriptionConfig:
    default_engine: str
    groq_api_key: str | None
    groq_api_url: str
    groq_model: str
    groq_max_bytes: int
    elevenlabs_api_key: str | None
    elevenlabs_api_url: str
    elevenlabs_model: str


def load_config() -> TranscriptionConfig:
    engine = os.environ.get("TRANSCRIBER", "groq").strip().lower()

    if engine not in ENGINES:
        raise ValueError(f"TRANSCRIBER must be one of {', '.join(ENGINES)}, got {engine!r}")

    return TranscriptionConfig(
        default_engine=engine,
        groq_api_key=os.environ.get("GROQ_API_KEY") or None,
        groq_api_url=os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/audio/transcriptions"),
        groq_model=os.environ.get("GROQ_MODEL", "whisper-large-v3"),
        # The free tier's cap is 25 MB; stay a little under it. Raise it on the dev tier (100 MB).
        groq_max_bytes=int(os.environ.get("GROQ_MAX_BYTES", str(24 * 1024 * 1024))),
        elevenlabs_api_key=os.environ.get("ELEVENLABS_API_KEY") or None,
        elevenlabs_api_url=os.environ.get("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1/speech-to-text"),
        elevenlabs_model=os.environ.get("ELEVENLABS_MODEL", "scribe_v2"),
    )


SUMMARIZERS = ("groq", "gemini")


@dataclass(frozen=True)
class SummaryConfig:
    default_engine: str
    groq_api_key: str | None
    groq_chat_url: str
    groq_model: str
    gemini_api_key: str | None
    gemini_chat_url: str
    gemini_model: str


def load_summary_config() -> SummaryConfig:
    engine = os.environ.get("SUMMARIZER", "groq").strip().lower()

    if engine not in SUMMARIZERS:
        raise ValueError(f"SUMMARIZER must be one of {', '.join(SUMMARIZERS)}, got {engine!r}")

    return SummaryConfig(
        default_engine=engine,
        groq_api_key=os.environ.get("GROQ_API_KEY") or None,
        groq_chat_url=os.environ.get("GROQ_CHAT_URL", "https://api.groq.com/openai/v1/chat/completions"),
        groq_model=os.environ.get("GROQ_SUMMARY_MODEL", "openai/gpt-oss-120b"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY") or None,
        # Google's OpenAI-compatible endpoint, so one client class serves both providers.
        gemini_chat_url=os.environ.get(
            "GEMINI_CHAT_URL", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        ),
        # Free-tier catalogs change often. If this id is retired, set GEMINI_SUMMARY_MODEL.
        gemini_model=os.environ.get("GEMINI_SUMMARY_MODEL", "gemini-2.5-flash-lite"),
    )


def warn_about_missing_keys(config: TranscriptionConfig, summary: SummaryConfig | None = None) -> None:
    for variable, value in (("GROQ_API_KEY", config.groq_api_key), ("ELEVENLABS_API_KEY", config.elevenlabs_api_key)):
        if value is None:
            logger.warning("%s is not set. /transcribe will answer 503 for that engine until it is.", variable)

    if summary is not None and summary.gemini_api_key is None:
        logger.warning("GEMINI_API_KEY is not set. /summarize will answer 503 for the gemini engine until it is.")
