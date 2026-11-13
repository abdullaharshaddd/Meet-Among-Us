"""Summarizer tests. No real API is called: requests.post is replaced with a fake."""

from __future__ import annotations

import json

import pytest

from ml import summarizer
from ml.config import SummaryConfig
from ml.transcription import base

SECRET = "sk-test-secret-value"

TURNS = [
    summarizer.Turn(index=1, speaker="Abdullah", start=2.0, text="Let us ship the demo on Friday."),
    summarizer.Turn(index=2, speaker="Vaniya", start=9.5, text="Theek hai, main slides bana deti hoon."),
    summarizer.Turn(index=3, speaker="Unclear", start=15.0, text="ہاں بالکل"),
]


def make_config(**changes) -> SummaryConfig:
    values = dict(
        default_engine="groq",
        groq_api_key=SECRET,
        groq_chat_url="https://groq.example/chat",
        groq_model="test-model",
        gemini_api_key=SECRET,
        gemini_chat_url="https://gemini.example/chat",
        gemini_model="test-gemini",
    )
    values.update(changes)

    return SummaryConfig(**values)


def good_reply(**changes) -> dict:
    reply = {
        "summary": [{"text": "Abdullah proposed shipping the demo on Friday.", "turns": [1]}],
        "key_points": [{"text": "Demo date.", "turns": [1]}],
        "decisions": [
            {"decision": "Ship the demo on Friday.", "decided_by": "Abdullah", "turns": [1], "quote": "ship the demo on Friday"}
        ],
        "action_items": [
            {
                "task": "Make the slides.",
                "owner": "Vaniya",
                "deadline": None,
                "turns": [2],
                "quote": "main slides bana deti hoon",
            }
        ],
    }
    reply.update(changes)

    return reply


class FakeResponse:
    def __init__(self, status_code: int = 200, content: str | None = None, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.headers = headers or {}
        self.text = text
        self._content = content

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def fake_post(monkeypatch: pytest.MonkeyPatch, *responses: FakeResponse) -> list[dict]:
    queue = list(responses)
    calls: list[dict] = []

    def post(url, **kwargs):
        calls.append({"url": url, **kwargs})

        return queue.pop(0)

    monkeypatch.setattr(summarizer.requests, "post", post)

    return calls


def reply_response(reply: dict | str) -> FakeResponse:
    return FakeResponse(content=reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False))


def groq() -> summarizer.ChatSummarizer:
    return summarizer.build_summarizer("groq", make_config())


def test_a_good_reply_is_parsed_and_passes_in_one_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, reply_response(good_reply()))

    result = summarizer.summarize_with_retry(groq(), TURNS)

    assert result.attempts == 1
    assert result.output.decisions[0].decided_by == "Abdullah"
    assert result.output.action_items[0].warnings == []
    assert result.output.decisions[0].warnings == []


def test_the_request_numbers_the_turns_and_never_leaks_the_key_into_the_body(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_post(monkeypatch, reply_response(good_reply()))

    summarizer.summarize_with_retry(groq(), TURNS)

    user_message = calls[0]["json"]["messages"][1]["content"]

    assert "[2] (00:09) Vaniya: Theek hai" in user_message
    assert SECRET not in json.dumps(calls[0]["json"])
    assert calls[0]["headers"]["Authorization"] == f"Bearer {SECRET}"


def test_broken_json_is_retried_once_with_the_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_post(monkeypatch, reply_response("not json at all"), reply_response(good_reply()))

    result = summarizer.summarize_with_retry(groq(), TURNS)

    assert result.attempts == 2
    assert "not valid JSON" in calls[1]["json"]["messages"][1]["content"]


def test_two_broken_replies_fail_clearly_and_the_message_has_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, reply_response("nope"), reply_response("still nope"))

    with pytest.raises(summarizer.SummaryFailedError) as caught:
        summarizer.summarize_with_retry(groq(), TURNS)

    assert caught.value.status_code == 502
    assert "twice" in str(caught.value)
    assert SECRET not in str(caught.value)


def test_a_turn_number_that_does_not_exist_triggers_a_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = good_reply(summary=[{"text": "Something.", "turns": [99]}])
    calls = fake_post(monkeypatch, reply_response(bad), reply_response(good_reply()))

    result = summarizer.summarize_with_retry(groq(), TURNS)

    assert result.attempts == 2
    assert "[99]" in calls[1]["json"]["messages"][1]["content"]


def test_an_item_with_no_turns_triggers_a_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = good_reply(key_points=[{"text": "No evidence.", "turns": []}])
    fake_post(monkeypatch, reply_response(bad), reply_response(good_reply()))

    assert summarizer.summarize_with_retry(groq(), TURNS).attempts == 2


def test_a_summary_of_nine_sentences_triggers_a_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    too_long = good_reply(summary=[{"text": f"Sentence {number}.", "turns": [1]} for number in range(9)])
    fake_post(monkeypatch, reply_response(too_long), reply_response(good_reply()))

    assert summarizer.summarize_with_retry(groq(), TURNS).attempts == 2


def test_a_decision_whose_quote_is_not_in_the_cited_turns_is_dropped_and_counted(monkeypatch: pytest.MonkeyPatch) -> None:
    reply = good_reply()
    reply["decisions"][0]["quote"] = "we will ship on Monday"
    fake_post(monkeypatch, reply_response(reply))

    result = summarizer.summarize_with_retry(groq(), TURNS)

    assert result.attempts == 1  # dropping is not a reason to ask the model again
    assert result.output.decisions == []
    assert (result.dropped_decisions, result.dropped_action_items) == (1, 0)
    assert len(result.output.action_items) == 1


def test_an_action_item_with_a_made_up_quote_is_dropped_and_the_supported_one_stays() -> None:
    reply = good_reply()
    reply["action_items"].append(
        {"task": "Book the room.", "owner": "Abdullah", "deadline": None, "turns": [1], "quote": "I will book the room"}
    )
    output = summarizer.read_reply(json.dumps(reply), TURNS)

    assert summarizer.finalize(output, TURNS) == (0, 1)
    assert [item.task for item in output.action_items] == ["Make the slides."]


def test_an_unnamed_voice_as_owner_becomes_owner_not_identified() -> None:
    for label in ("Unclear", "Unknown Speaker 3"):
        reply = good_reply()
        reply["action_items"][0]["owner"] = label
        output = summarizer.read_reply(json.dumps(reply), TURNS)
        summarizer.finalize(output, TURNS)

        assert output.action_items[0].owner == "owner not identified"
        assert not any(warning.startswith("owner") for warning in output.action_items[0].warnings)


def test_a_named_owner_is_left_alone() -> None:
    output = summarizer.read_reply(json.dumps(good_reply()), TURNS)
    summarizer.finalize(output, TURNS)

    assert output.action_items[0].owner == "Vaniya"


def test_a_deadline_that_is_not_in_the_cited_turns_is_removed() -> None:
    reply = good_reply()
    reply["action_items"][0]["deadline"] = "next Tuesday"
    output = summarizer.read_reply(json.dumps(reply), TURNS)
    summarizer.finalize(output, TURNS)

    assert output.action_items[0].deadline is None
    assert output.action_items[0].warnings == ["The deadline was removed: it is not in the cited turns."]


def test_quotes_match_after_case_and_punctuation_and_in_urdu_script() -> None:
    reply = good_reply()
    reply["decisions"][0]["quote"] = "Ship the demo on FRIDAY!"
    reply["key_points"] = [{"text": "Agreement.", "turns": [3]}]
    reply["action_items"][0]["turns"] = [3]
    reply["action_items"][0]["quote"] = "ہاں، بالکل۔"
    reply["action_items"][0]["owner"] = "Vaniya"

    output = summarizer.read_reply(json.dumps(reply, ensure_ascii=False), TURNS)

    assert output.decisions[0].warnings == []
    assert output.action_items[0].warnings == []


def test_an_owner_who_is_not_a_speaker_or_in_the_text_is_a_warning() -> None:
    reply = good_reply()
    reply["action_items"][0]["owner"] = "Sana"

    output = summarizer.read_reply(json.dumps(reply), TURNS)

    assert "owner 'Sana' is not a speaker" in output.action_items[0].warnings[0]


def test_unclear_as_an_owner_and_a_deadline_not_in_the_text_are_warnings() -> None:
    reply = good_reply()
    reply["action_items"][0]["owner"] = "Unclear"
    reply["action_items"][0]["deadline"] = "next Tuesday"

    output = summarizer.read_reply(json.dumps(reply), TURNS)

    assert any("not a person" in warning for warning in output.action_items[0].warnings)
    assert "The deadline is not in the cited turns." in output.action_items[0].warnings


def test_a_deadline_that_was_said_has_no_warning() -> None:
    reply = good_reply()
    reply["action_items"][0].update(turns=[1], quote="ship the demo on Friday", owner="Abdullah", deadline="Friday")

    output = summarizer.read_reply(json.dumps(reply), TURNS)

    assert output.action_items[0].warnings == []


def test_empty_decisions_and_action_items_are_fine() -> None:
    output = summarizer.read_reply(json.dumps(good_reply(decisions=[], action_items=[])), TURNS)

    assert output.decisions == [] and output.action_items == []


def test_a_missing_key_answers_503_naming_the_variable() -> None:
    no_key = summarizer.build_summarizer("gemini", make_config(gemini_api_key=None))

    with pytest.raises(base.MissingApiKeyError) as caught:
        no_key.summarize(TURNS, None)

    assert caught.value.status_code == 503
    assert "GEMINI_API_KEY" in str(caught.value)


def test_a_413_says_the_transcript_is_too_long_and_suggests_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, FakeResponse(status_code=413, text="Request too large"))

    with pytest.raises(summarizer.TranscriptTooLongError) as caught:
        groq().summarize(TURNS, None)

    assert "engine=gemini" in str(caught.value)


def test_a_rate_limit_is_retried_by_the_shared_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(base, "sleep", sleeps.append)
    fake_post(monkeypatch, FakeResponse(status_code=429), reply_response(good_reply()))

    assert summarizer.summarize_with_retry(groq(), TURNS).attempts == 1
    assert len(sleeps) == 1


def test_a_provider_error_message_carries_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_post(monkeypatch, FakeResponse(status_code=500, text="upstream broke"))

    with pytest.raises(base.ProviderError) as caught:
        groq().summarize(TURNS, None)

    assert SECRET not in str(caught.value)


def test_an_unnamed_voice_as_decided_by_becomes_speaker_not_identified() -> None:
    for label in ("Unclear", "Unknown Speaker 2"):
        reply = good_reply()
        reply["decisions"][0]["decided_by"] = label
        output = summarizer.read_reply(json.dumps(reply), TURNS)
        summarizer.finalize(output, TURNS)

        assert output.decisions[0].decided_by == "speaker not identified"
        assert not any(warning.startswith("decided_by") for warning in output.decisions[0].warnings)


def test_a_named_decided_by_is_left_alone() -> None:
    output = summarizer.read_reply(json.dumps(good_reply()), TURNS)
    summarizer.finalize(output, TURNS)

    assert output.decisions[0].decided_by == "Abdullah"
