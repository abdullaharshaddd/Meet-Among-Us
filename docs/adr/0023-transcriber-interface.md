# 0023 — One transcriber interface, Whisper as the default

## Context

Transcription turns a clip into words with times. Speaker labels come from our own voiceprint
matching (ADR-0020), so the engine only has to supply words. We need to compare engines on the
same clips, and Urdu mixed with English is the hard case: Whisper can drift into Devanagari
(Hindi script) or spell English words in Urdu letters.

## Options considered

- **One hard-wired engine.** Simplest, but no way to compare, and a rate limit or outage is fatal.
- **Engine-side diarization.** Gives speakers for free, but they would not be our enrolled people.
- **A small interface with two implementations, chosen by config or per request.**

## Decision

`ml/ml/transcription/` holds a `Transcriber` interface with two engines that return the same
shape (words with text, start, end, plus the engine's detected language):

- **Groq Whisper (`whisper-large-v3`) is the default.** Whisper is open-weight, so it can be
  fine-tuned later on our own Urdu and code-switched recordings and compared against this baseline.
- **ElevenLabs Scribe (`scribe_v2`)** is the comparison engine, with its own diarization turned off.
- `TRANSCRIBER` picks the default and the `engine` request parameter overrides it, so one clip can
  go through both.
- Urdu requests pass `language=ur` and a short Urdu prompt with English work words in English letters
  (Groq only; Scribe has no prompt field). Any Devanagari in the output is reported as `script_warning`.
- Audio is converted to 16 kHz mono FLAC. If it is still over Groq's size limit it is split at the
  longest silence in the back half of each chunk, and timestamps are shifted back onto one timeline.
  With no silence to cut at, the cut falls at the limit and may split a word.
- A 429 is retried 3 times with growing waits (or the provider's `retry-after`), then fails with a
  clear message. Keys are never logged or put in error text.
- A missing key never stops the ML service from starting, since it also handles enrollment. It logs a
  warning at boot, and `/transcribe` answers 503 naming the variable to set.
- In the backend, each word goes to the speaker turn it overlaps most. A word in a gap joins the
  nearest turn if within `word_attach_max_gap_sec` (1.0 s), otherwise it shows as "Unclear". Entries
  carry the turn's evidence (best score, margin, pooled seconds, floor applied).

## Consequences

- An entry's language comes from the script of its text, not from the engine. Urdu written in English
  letters (Roman Urdu) is labelled `en`.
- The engine's own file-level language is returned separately as `engine_language`.
- Both engines send audio to a third party. That is acceptable for development, but the Phase 6
  consent screen must cover it before real meeting audio goes through.
- Nothing is saved yet and there is no schema change.
