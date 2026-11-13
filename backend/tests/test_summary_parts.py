"""Split-then-merge summaries. No database and no network: the ML call is replaced by a fake."""

import pytest

from app.core import ml_client
from app.core.exceptions import SummaryTooLongError
from app.services import summary_service


def make_turns(count: int, text: str = "x" * 100) -> list[dict]:
    return [{"index": number, "speaker": "Host", "start": float(number), "text": text} for number in range(1, count + 1)]


def summary_for(turns: list[dict]) -> ml_client.MLSummary:
    """What the fake model says about a part: it cites the first and last turn it was shown."""
    first, last = turns[0]["index"], turns[-1]["index"]

    return ml_client.MLSummary(
        engine="groq",
        model="m",
        attempts=1,
        dropped_decisions=0,
        dropped_action_items=1,
        summary=[ml_client.MLPoint(text=f"Part {first}-{last}", turns=[first, last], warnings=[])],
        key_points=[ml_client.MLPoint(text="Same point", turns=[first], warnings=[])],
        decisions=[ml_client.MLDecision(decision=f"Decide {first}", decided_by=None, turns=[first], quote="q", warnings=[])],
        action_items=[
            ml_client.MLActionItem(task="Same task", owner=None, deadline=None, turns=[last], quote="q", warnings=[])
        ],
    )


def test_a_short_transcript_stays_in_one_part() -> None:
    parts = summary_service.split_into_parts(make_turns(3), 6000)

    assert len(parts) == 1 and len(parts[0]) == 3


def test_a_long_transcript_is_cut_between_turns_and_keeps_every_turn_in_order() -> None:
    turns = make_turns(20)

    parts = summary_service.split_into_parts(turns, 500)

    assert len(parts) > 1
    assert [turn["index"] for part in parts for turn in part] == list(range(1, 21))
    assert all(len(part) >= 1 for part in parts)


def test_one_turn_bigger_than_the_limit_goes_alone_instead_of_being_cut() -> None:
    parts = summary_service.split_into_parts(make_turns(1, "y" * 10_000), 500)

    assert len(parts) == 1 and len(parts[0]) == 1


def test_each_part_is_summarized_with_the_original_turn_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[int]] = []

    def fake(part, engine):
        seen.append([turn["index"] for turn in part])

        return summary_for(part)

    monkeypatch.setattr(ml_client, "summarize", fake)
    monkeypatch.setattr(summary_service.settings, "summary_part_max_chars", 500)

    merged = summary_service.summarize_turns(make_turns(20), None)

    # The second part starts at a turn number above 1, so its citations point at the real turns.
    assert seen[0][0] == 1 and seen[1][0] > 1
    assert merged.parts == len(seen) and merged.parts > 1
    cited = [turn for point in merged.summary for turn in point.turns]
    assert cited == sorted(cited) and max(cited) == 20


def test_merging_keeps_sentences_in_order_adds_the_counts_and_dedupes_repeats(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ml_client, "summarize", lambda part, engine: summary_for(part))
    monkeypatch.setattr(summary_service.settings, "summary_part_max_chars", 500)

    merged = summary_service.summarize_turns(make_turns(20), None)

    assert len(merged.summary) == merged.parts
    assert [point.text for point in merged.key_points] == ["Same point"]
    assert [action.task for action in merged.action_items] == ["Same task"]
    assert len(merged.decisions) == merged.parts
    assert merged.dropped_action_items == merged.parts


def test_a_part_the_provider_says_is_too_long_is_halved_and_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake(part, engine):
        calls.append(len(part))

        if len(part) > 4:
            raise SummaryTooLongError("too long")

        return summary_for(part)

    monkeypatch.setattr(ml_client, "summarize", fake)

    merged = summary_service.summarize_turns(make_turns(8), None)

    assert calls == [8, 4, 4]
    assert merged.parts == 2
    assert [turn for point in merged.summary for turn in point.turns] == [1, 4, 5, 8]


def test_a_single_turn_that_is_still_too_long_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    def always_too_long(part, engine):
        raise SummaryTooLongError("too long")

    monkeypatch.setattr(ml_client, "summarize", always_too_long)

    with pytest.raises(SummaryTooLongError):
        summary_service.summarize_turns(make_turns(1), None)
