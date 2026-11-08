"""Transcription tests. No real API is called: requests.post is replaced with a fake, and
VAD is stubbed where splitting is tested."""

from __future__ import annotations

import numpy as np
import pytest
import requests

from ml.config import TranscriptionConfig
from ml.transcription import base, engines, pipeline

SECRET = "sk-test-secret-value"


def make_config(**changes) -> TranscriptionConfig:
    values = dict(
        default_engine="groq",
        groq_api_key=SECRET,
        groq_api_url="https://groq.example/transcribe",
        groq_model="whisper-large-v3",
        groq_max_bytes=24 * 1024 * 1024,
        elevenlabs_api_key=SECRET,
        elevenlabs_api_url="https://eleven.example/stt",
        elevenlabs_model="scribe_v2",
    )
    values.update(changes)

    return TranscriptionConfig(**values)


class FakeResponse:
    def __init__(self, status_code: int = 200, body: dict | None = None, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._body = body if body is not None else {}
        self.headers = headers or {}
        self.text = text

    def json(self) -> dict:
        return self._body


@pytest.fixture()
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(base, "sleep", recorded.append)

    return recorded


def fake_post(monkeypatch: pytest.MonkeyPatch, *responses: FakeResponse) -> list[dict]:
    queue = list(responses)
    calls: list[dict] = []

    def post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        item = queue.pop(0)

        if isinstance(item, Exception):
            raise item

        return item

    monkeypatch.setattr(engines.requests, "post", post)

    return calls


GROQ_BODY = {
    "language": "urdu",
    "words": [{"word": " یار", "start": 0.1, "end": 0.4}, {"word": "deadline", "start": 0.5, "end": 1.0}],
}

ELEVEN_BODY = {
    "language_code": "urd",
    "words": [
        {"text": "یار", "type": "word", "start": 0.1, "end": 0.4, "speaker_id": "speaker_0"},
        {"text": " ", "type": "spacing", "start": 0.4, "end": 0.5},
        {"text": "(laughter)", "type": "audio_event", "start": 0.5, "end": 0.9},
        {"text": "deadline", "type": "word", "start": 0.9, "end": 1.4},
    ],
}


def test_groq_words_are_normalised(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, FakeResponse(body=GROQ_BODY))
    transcript = engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    assert transcript.language == "urdu"
    assert [(w.text, w.start, w.end) for w in transcript.words] == [("یار", 0.1, 0.4), ("deadline", 0.5, 1.0)]


def test_elevenlabs_keeps_only_real_words_and_ignores_its_speakers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, FakeResponse(body=ELEVEN_BODY))
    transcript = engines.ElevenLabsScribeTranscriber(make_config()).transcribe(b"flac", "ur")

    assert transcript.language == "urd"
    assert [w.text for w in transcript.words] == ["یار", "deadline"]


def test_groq_request_asks_for_word_timestamps_and_steers_urdu(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_post(monkeypatch, FakeResponse(body=GROQ_BODY), FakeResponse(body=GROQ_BODY), FakeResponse(body=GROQ_BODY))
    transcriber = engines.GroqWhisperTranscriber(make_config())

    transcriber.transcribe(b"flac", "ur")
    transcriber.transcribe(b"flac", "en")
    transcriber.transcribe(b"flac", None)

    urdu, english, auto = (call["data"] for call in calls)
    assert urdu["response_format"] == "verbose_json"
    assert urdu["timestamp_granularities[]"] == "word"
    assert urdu["model"] == "whisper-large-v3"
    assert urdu["language"] == "ur" and urdu["prompt"] == base.URDU_PROMPT
    assert "prompt" not in english
    assert "language" not in auto
    assert calls[0]["url"] == "https://groq.example/transcribe"


def test_elevenlabs_request_turns_its_own_diarization_off(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_post(monkeypatch, FakeResponse(body=ELEVEN_BODY))
    engines.ElevenLabsScribeTranscriber(make_config()).transcribe(b"flac", "ur")

    form = calls[0]["data"]
    assert form["diarize"] == "false"
    assert form["timestamps_granularity"] == "word"
    assert form["model_id"] == "scribe_v2"
    assert calls[0]["headers"] == {"xi-api-key": SECRET}


def test_rate_limit_is_retried_then_succeeds(monkeypatch: pytest.MonkeyPatch, sleeps: list[float]) -> None:
    fake_post(monkeypatch, FakeResponse(429), FakeResponse(body=GROQ_BODY))
    transcript = engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    assert len(transcript.words) == 2
    assert sleeps == [1.0]


def test_rate_limit_gives_up_after_three_retries_with_a_clear_message(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    fake_post(monkeypatch, *[FakeResponse(429)] * 4)

    with pytest.raises(base.RateLimitedError) as caught:
        engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    assert sleeps == [1.0, 2.0, 4.0]
    assert "after 3 retries" in str(caught.value)
    assert caught.value.status_code == 429


def test_retry_after_header_is_honoured(monkeypatch: pytest.MonkeyPatch, sleeps: list[float]) -> None:
    fake_post(monkeypatch, FakeResponse(429, headers={"retry-after": "7"}), FakeResponse(body=GROQ_BODY))
    engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    assert sleeps == [7.0]


def test_api_key_never_appears_in_error_text(monkeypatch: pytest.MonkeyPatch, sleeps: list[float]) -> None:
    fake_post(monkeypatch, FakeResponse(500, text="upstream exploded"))

    with pytest.raises(base.ProviderError) as server_error:
        engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    fake_post(monkeypatch, requests.ConnectionError(f"failed with Authorization: Bearer {SECRET}"))

    with pytest.raises(base.ProviderError) as network_error:
        engines.GroqWhisperTranscriber(make_config()).transcribe(b"flac", "ur")

    assert SECRET not in str(server_error.value)
    assert SECRET not in str(network_error.value)


def test_missing_key_names_the_variable_to_set() -> None:
    with pytest.raises(base.MissingApiKeyError) as groq_error:
        engines.GroqWhisperTranscriber(make_config(groq_api_key=None)).transcribe(b"flac", "ur")

    with pytest.raises(base.MissingApiKeyError) as eleven_error:
        engines.ElevenLabsScribeTranscriber(make_config(elevenlabs_api_key=None)).transcribe(b"flac", "ur")

    assert "GROQ_API_KEY" in str(groq_error.value)
    assert "ELEVENLABS_API_KEY" in str(eleven_error.value)
    assert groq_error.value.status_code == 503


def test_devanagari_output_is_flagged() -> None:
    hindi = [base.Word("यार", 0.0, 0.3), base.Word("deadline", 0.4, 0.9)]
    urdu = [base.Word("یار", 0.0, 0.3), base.Word("deadline", 0.4, 0.9)]

    assert "Devanagari" in base.script_warning(hindi)
    assert base.script_warning(urdu) is None


def test_cut_goes_at_the_longest_silence_in_the_back_half() -> None:
    speech = [(0.0, 4.0), (4.2, 8.0), (9.0, 12.0)]

    assert pipeline.choose_cuts(speech, 12.0, 10.0) == [8.5]


def test_cut_falls_back_to_the_limit_when_there_is_no_silence() -> None:
    assert pipeline.choose_cuts([(0.0, 12.0)], 12.0, 5.0) == [5.0, 10.0]


class CountingTranscriber:
    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def transcribe(self, flac_bytes: bytes, language: str | None) -> base.Transcript:
        self.calls += 1

        return base.Transcript(language="ur", words=[base.Word("w", 0.5, 1.0)])


def test_big_file_is_split_at_silence_and_timestamps_are_shifted_back(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_rate = 16000
    noise = np.random.default_rng(0).uniform(-0.3, 0.3, 8 * sample_rate).astype(np.float32)
    monkeypatch.setattr(pipeline.vad, "detect_speech_intervals", lambda s, r: [(0.0, 2.0), (2.6, 5.0), (5.4, 8.0)])
    bytes_per_second = len(pipeline.to_flac(noise, sample_rate)) / 8
    max_bytes = int(3.5 * bytes_per_second / pipeline.SIZE_SAFETY)
    transcriber = CountingTranscriber()

    transcript, requests_made = pipeline.transcribe_samples(noise, sample_rate, transcriber, "ur", max_bytes)

    assert requests_made == 3 and transcriber.calls == 3
    assert [round(word.start, 1) for word in transcript.words] == [0.5, 2.8, 5.7]


def test_small_file_is_sent_in_one_request() -> None:
    sample_rate = 16000
    quiet = np.zeros(sample_rate, dtype=np.float32)
    transcriber = CountingTranscriber()

    _, requests_made = pipeline.transcribe_samples(quiet, sample_rate, transcriber, "ur", 10_000_000)

    assert requests_made == 1 and transcriber.calls == 1
