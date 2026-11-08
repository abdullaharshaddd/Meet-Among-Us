"""Puts words (what was said) onto speaker turns (who said it). See
docs/adr/0023-transcriber-interface.md for the engines and why the speaker labels stay ours.
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.core.config import SpeakerIdSettings, speaker_id_settings
from app.models.user import User
from app.schemas.speaker_id import SpeakerTurn
from app.schemas.transcript import TranscribeResponse, TranscriptEntry
from app.services import speaker_id_service

ARABIC_SCRIPT = re.compile("[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
LATIN = re.compile("[A-Za-z]")

# A text counts as one language when at least this share of its letters are in that script.
SINGLE_LANGUAGE_SHARE = 0.9


def entry_language(text: str) -> str:
    urdu_letters = len(ARABIC_SCRIPT.findall(text))
    latin_letters = len(LATIN.findall(text))
    total = urdu_letters + latin_letters

    if total == 0:
        return "unknown"

    if urdu_letters / total >= SINGLE_LANGUAGE_SHARE:
        return "ur"

    if latin_letters / total >= SINGLE_LANGUAGE_SHARE:
        return "en"

    return "mixed"


def turn_for_word(word: ml_client.TranscribedWord, turns: list[SpeakerTurn], max_gap_sec: float) -> int | None:
    """The turn the word overlaps most. A word in a gap between turns goes to the nearest
    one if it is close enough, otherwise it belongs to no turn."""
    if not turns:
        return None

    overlaps = [max(0.0, min(word.end, turn.end) - max(word.start, turn.start)) for turn in turns]

    if max(overlaps) > 0:
        return overlaps.index(max(overlaps))

    gaps = [max(turn.start - word.end, word.start - turn.end, 0.0) for turn in turns]
    nearest = gaps.index(min(gaps))

    return nearest if gaps[nearest] <= max_gap_sec else None


def assign_words(
    words: list[ml_client.TranscribedWord], turns: list[SpeakerTurn], settings: SpeakerIdSettings
) -> list[TranscriptEntry]:
    runs: list[tuple[int | None, list[ml_client.TranscribedWord]]] = []

    for word in sorted(words, key=lambda item: item.start):
        index = turn_for_word(word, turns, settings.word_attach_max_gap_sec)

        if runs and runs[-1][0] == index:
            runs[-1][1].append(word)
        else:
            runs.append((index, [word]))

    return [_build_entry(turns[index] if index is not None else None, group) for index, group in runs]


def _build_entry(turn: SpeakerTurn | None, words: list[ml_client.TranscribedWord]) -> TranscriptEntry:
    text = " ".join(word.text for word in words)
    shared = dict(text=text, language=entry_language(text), start=words[0].start, end=words[-1].end)

    if turn is None:
        return TranscriptEntry(
            speaker_label="Unclear",
            user_id=None,
            best_candidate_name=None,
            best_score=None,
            runner_up_name=None,
            runner_up_score=None,
            margin=None,
            pooled_seconds=0.0,
            floor_applied=None,
            **shared,
        )

    return TranscriptEntry(
        speaker_label=turn.speaker_label,
        user_id=turn.user_id,
        best_candidate_name=turn.best_candidate_name,
        best_score=turn.best_score,
        runner_up_name=turn.runner_up_name,
        runner_up_score=turn.runner_up_score,
        margin=turn.margin,
        pooled_seconds=turn.pooled_seconds,
        floor_applied=turn.floor_applied,
        **shared,
    )


def transcribe(
    db: Session,
    user: User,
    workspace_id: UUID,
    audio_key: str,
    engine: str | None,
    settings: SpeakerIdSettings = speaker_id_settings,
) -> TranscribeResponse:
    speaker_id_service.require_clip_access(db, user, workspace_id, audio_key)
    audio_bytes = storage.get_object_bytes(audio_key)

    # Transcribing first, so a missing API key fails before the slower speaker work starts.
    transcript = ml_client.transcribe(audio_bytes, engine)
    identified = speaker_id_service.identify_audio(db, workspace_id, audio_bytes, settings)

    return TranscribeResponse(
        engine=transcript.engine,
        engine_language=transcript.language,
        script_warning=transcript.script_warning,
        duration_sec=transcript.duration_sec,
        entries=assign_words(transcript.words, identified.turns, settings),
        skipped_voiceprints=identified.skipped_voiceprints,
    )
