"""Turns a numbered transcript into a summary, decisions and action items with an LLM.

See docs/adr/0025-summarization-model-choice.md for the models and
docs/adr/0026-grounding-with-turn-citations.md for how every claim is tied to transcript turns.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

import requests
from pydantic import BaseModel, Field, ValidationError

from ml.config import SummaryConfig
from ml.transcription.base import MissingApiKeyError, ProviderError, TranscriptionError, post_with_retry

TIMEOUT_SEC = 120
MAX_SUMMARY_SENTENCES = 8

# Groq counts the room left for the answer against its tokens-per-minute limit, so a huge
# default would make a short transcript look too long.
MAX_ANSWER_TOKENS = 3000

SYSTEM_PROMPT = """You summarise one meeting transcript. The speakers mix Urdu and English.
Use ONLY what the transcript says. Do not add facts, names, dates or reasons that are not in it.

Each line of the transcript looks like:  [3] (01:42) Speaker name: words that were said
The number in square brackets is the turn number. Cite turns by that number and nothing else.

Write the summary, key points, decisions and action items in English. Keep names, technical terms
and quotes exactly as spoken, in their original script. Never translate or transliterate a quote.

Answer with one JSON object and nothing else, with exactly these keys:
{
  "summary":      [{"text": "one sentence", "turns": [3, 4]}],
  "key_points":   [{"text": "a discussion point", "turns": [3]}],
  "decisions":    [{"decision": "what was decided", "decided_by": "speaker or null", "turns": [5], "quote": "words copied from a cited turn"}],
  "action_items": [{"task": "what must be done", "owner": "person or null", "deadline": "as said, or null", "turns": [6], "quote": "words copied from a cited turn"}]
}

Rules:
- "summary" has one sentence per item, 5 to 8 items. If the transcript is too short for 5, write fewer. Never pad.
- Every item needs at least one turn number that appears in the transcript, and those turns must support the item.
- "quote" is copied word for word from one of the cited turns, in its original script.
- Only list a decision or an action item that the speakers EXPLICITLY said. A decision needs words showing it was settled or agreed ("let's decide", "agreed", "okay, we'll do X"). An action item needs someone taking or being given the task in so many words ("I will do X by Friday", "you handle X"). Do not infer either from a status update, a plan mentioned in passing, a wish, a question or something already done.
- The task or decision itself must be stated in the cited turns. Do not complete it from other turns or from phrases like "as discussed".
- A suggestion nobody accepted is a key point, not a decision. A topic that was only discussed is a key point, not an action item.
- If you are unsure whether something was explicitly said, leave it out. An empty list is a correct answer; most short exchanges have no decisions or no action items.
- "decided_by" is the speaker who proposed or made the decision. Use the speaker label exactly as it appears, or null if it is not clear.
- "owner" is the speaker who took the task, or the person the speakers said would do it. Use null if nobody was named.
- "deadline" is only a deadline someone actually said, copied as said. Otherwise null.
- "Unknown Speaker 1", "Unknown Speaker 2" and "Unclear" are labels, not people. Never call them guests, and never use "Unclear" as an owner or as "decided_by".
- The transcript comes from speech recognition and may contain mistakes. Do not guess a correction.
- If there are no decisions or no action items, return an empty list. Never invent one.
"""


class TranscriptTooLongError(TranscriptionError):
    status_code = 413


class SummaryFailedError(TranscriptionError):
    status_code = 502


class Turn(BaseModel):
    index: int  # the number the model cites
    speaker: str
    start: float
    text: str


class Point(BaseModel):
    text: str
    turns: list[int] = Field(min_length=1)
    warnings: list[str] = []


class Decision(BaseModel):
    decision: str
    decided_by: str | None = None
    turns: list[int] = Field(min_length=1)
    quote: str
    warnings: list[str] = []
    # Set when decided_by was an unnamed voice ("Unknown Speaker 2"). decided_by then reads "speaker not
    # identified", and this keeps which voice it was, so a later rename can still find it.
    unnamed_label: str | None = None


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None
    turns: list[int] = Field(min_length=1)
    quote: str
    warnings: list[str] = []
    unnamed_label: str | None = None  # as for Decision, for owner


class SummaryOutput(BaseModel):
    summary: list[Point]
    key_points: list[Point]
    decisions: list[Decision]
    action_items: list[ActionItem]


@dataclass(frozen=True)
class SummaryResult:
    output: SummaryOutput
    attempts: int
    dropped_decisions: int = 0  # decisions removed because their cited turns do not contain the quote
    dropped_action_items: int = 0


class Summarizer(Protocol):
    name: str
    model: str

    def summarize(self, turns: list[Turn], previous_problems: str | None) -> str:
        """Returns the model's raw reply text. Checking it is the same for every provider."""
        ...


class BadReply(Exception):
    """The model's reply was rejected. The message says why, and is sent back on the retry."""


def clock(seconds: float) -> str:
    minutes, rest = divmod(int(seconds), 60)

    return f"{minutes:02d}:{rest:02d}"


def format_transcript(turns: list[Turn]) -> str:
    return "\n".join(f"[{turn.index}] ({clock(turn.start)}) {turn.speaker}: {turn.text}" for turn in turns)


class ChatSummarizer:
    """Any provider that speaks the OpenAI chat-completions format. Groq and Gemini both do."""

    def __init__(self, name: str, chat_url: str, api_key: str | None, key_variable: str, model: str) -> None:
        self.name = name
        self.chat_url = chat_url
        self.api_key = api_key
        self.key_variable = key_variable
        self.model = model

    def summarize(self, turns: list[Turn], previous_problems: str | None) -> str:
        if not self.api_key:
            raise MissingApiKeyError(self.key_variable)

        provider = self.name.capitalize()
        transcript = format_transcript(turns)

        if previous_problems:
            transcript += f"\n\nYour last answer was rejected: {previous_problems}\nAnswer again with corrected JSON only."

        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,  # low, so the same transcript gives nearly the same summary
            "max_tokens": MAX_ANSWER_TOKENS,
        }

        def send() -> requests.Response:
            response = requests.post(
                self.chat_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=request_body,
                timeout=TIMEOUT_SEC,
            )

            if response.status_code == 413:
                raise TranscriptTooLongError(
                    f"The transcript is too long for {provider} in one request. "
                    "Try the other summarizer (engine=gemini), or summarize a shorter clip."
                )

            return response

        response = post_with_retry(send, provider)

        return _reply_text(response, provider)


def _reply_text(response: requests.Response, provider: str) -> str:
    try:
        return response.json()["choices"][0]["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError):
        raise ProviderError(f"{provider} returned a reply in an unexpected shape.") from None


def build_summarizer(engine: str, config: SummaryConfig) -> ChatSummarizer:
    if engine == "groq":
        return ChatSummarizer("groq", config.groq_chat_url, config.groq_api_key, "GROQ_API_KEY", config.groq_model)

    return ChatSummarizer("gemini", config.gemini_chat_url, config.gemini_api_key, "GEMINI_API_KEY", config.gemini_model)


def normalize(text: str) -> str:
    # Lower case and drop punctuation so "Friday." matches "friday". \w keeps Urdu letters.
    return " ".join(re.sub(r"[\W_]+", " ", text.casefold()).split())


def read_reply(raw: str, turns: list[Turn]) -> SummaryOutput:
    try:
        data = json.loads(raw)
    except ValueError:
        raise BadReply("The reply was not valid JSON.") from None

    try:
        output = SummaryOutput.model_validate(data)
    except ValidationError as error:
        details = "; ".join(f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in error.errors()[:5])
        raise BadReply(f"The JSON did not match the format. {details}") from None

    problems = hard_problems(output, {turn.index for turn in turns})

    if problems:
        raise BadReply(" ".join(problems))

    add_warnings(output, turns)

    return output


def hard_problems(output: SummaryOutput, valid_turns: set[int]) -> list[str]:
    problems = []

    if not 1 <= len(output.summary) <= MAX_SUMMARY_SENTENCES:
        problems.append(f"The summary must have 1 to {MAX_SUMMARY_SENTENCES} sentences, it had {len(output.summary)}.")

    sections = (
        ("summary", output.summary),
        ("key_points", output.key_points),
        ("decisions", output.decisions),
        ("action_items", output.action_items),
    )

    for section_name, items in sections:
        for item in items:
            unknown = [number for number in item.turns if number not in valid_turns]

            if unknown:
                problems.append(f"{section_name} cites turn(s) {unknown}, which are not in the transcript.")

    return problems


def add_warnings(output: SummaryOutput, turns: list[Turn]) -> None:
    """Soft checks. An Urdu spelling variant should not cost a retry, so these only mark the item."""
    turn_by_number = {turn.index: turn for turn in turns}
    speakers = {normalize(turn.speaker) for turn in turns}

    for decision in output.decisions:
        cited_text = _cited_text(decision.turns, turn_by_number)
        decision.warnings = _quote_warnings(decision.quote, cited_text)
        decision.warnings += _person_warnings("decided_by", decision.decided_by, speakers, cited_text)

    for action in output.action_items:
        cited_text = _cited_text(action.turns, turn_by_number)
        action.warnings = _quote_warnings(action.quote, cited_text)
        action.warnings += _person_warnings("owner", action.owner, speakers, cited_text)

        if action.deadline and normalize(action.deadline) not in cited_text:
            action.warnings.append(DEADLINE_MISSING)


def _cited_text(turn_numbers: list[int], turn_by_number: dict[int, Turn]) -> str:
    return normalize(" ".join(turn_by_number[number].text for number in turn_numbers))


def _quote_warnings(quote: str, cited_text: str) -> list[str]:
    wanted = normalize(quote)

    if not wanted or wanted not in cited_text:
        return [QUOTE_MISSING]

    return []


def _person_warnings(field: str, name: str | None, speakers: set[str], cited_text: str) -> list[str]:
    if not name:
        return []

    wanted = normalize(name)

    if wanted == "unclear":
        return [f"{field} is 'Unclear', which is not a person."]

    if wanted not in speakers and wanted not in cited_text:
        return [f"{field} '{name}' is not a speaker and is not in the cited turns."]

    return []


QUOTE_MISSING = "The quote is not found in the cited turns."
DEADLINE_MISSING = "The deadline is not in the cited turns."
OWNER_NOT_IDENTIFIED = "owner not identified"
SPEAKER_NOT_IDENTIFIED = "speaker not identified"
# Matches the labels the transcript gives to voices it could not name. They are not people.
UNNAMED_SPEAKER = re.compile(r"unknown speaker \d+|unclear")


def finalize(output: SummaryOutput, turns: list[Turn]) -> tuple[int, int]:
    """Enforces what the soft checks found, in place. Returns (decisions dropped, action items dropped).

    An item whose quote is not in the turns it cites is not backed by the transcript, so it goes.
    A deadline that is not in those turns is removed rather than shown as if it were said.
    An owner or decided_by that is an unnamed voice reads "owner not identified" or
    "speaker not identified" instead of a label.
    """
    decisions, actions = len(output.decisions), len(output.action_items)
    output.decisions = [item for item in output.decisions if QUOTE_MISSING not in item.warnings]
    output.action_items = [item for item in output.action_items if QUOTE_MISSING not in item.warnings]

    for decision in output.decisions:
        if decision.decided_by and UNNAMED_SPEAKER.fullmatch(normalize(decision.decided_by)):
            decision.unnamed_label = decision.decided_by
            decision.decided_by = SPEAKER_NOT_IDENTIFIED
            decision.warnings = [w for w in decision.warnings if not w.startswith("decided_by")]

    for action in output.action_items:
        if DEADLINE_MISSING in action.warnings:
            action.deadline = None
            action.warnings = [w if w != DEADLINE_MISSING else "The deadline was removed: it is not in the cited turns." for w in action.warnings]

        if action.owner and UNNAMED_SPEAKER.fullmatch(normalize(action.owner)):
            action.unnamed_label = action.owner
            action.owner = OWNER_NOT_IDENTIFIED
            action.warnings = [w for w in action.warnings if not w.startswith("owner")]

    return decisions - len(output.decisions), actions - len(output.action_items)


def summarize_with_retry(summarizer: Summarizer, turns: list[Turn]) -> SummaryResult:
    """One retry with the reasons sent back to the model, then a clear failure."""
    problems: str | None = None

    for attempt in (1, 2):
        raw = summarizer.summarize(turns, problems)

        try:
            output = read_reply(raw, turns)
            dropped_decisions, dropped_action_items = finalize(output, turns)

            return SummaryResult(output, attempt, dropped_decisions, dropped_action_items)
        except BadReply as error:
            problems = str(error)

    raise SummaryFailedError(f"{summarizer.name} gave a reply that failed the checks twice. Last reason: {problems}")
