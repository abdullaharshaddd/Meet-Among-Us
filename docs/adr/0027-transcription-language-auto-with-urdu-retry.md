# 0027 — Transcription language: auto-detect, retry as Urdu on Devanagari

## Context

ADR-0023 forced `language=ur` on every request. On `Recordings/English.ogg` (English speech) that
produced a transcript in phonetic Urdu script, and the summary of it was nonsense. The product is
mostly Urdu-English, but meetings can be mostly English.

## Options considered

- **Keep forcing Urdu.** Breaks English-heavy meetings.
- **Auto-detect only.** Fixes English. But on the two mixed clips Whisper named the language
  "Hindi" and wrote 117–119 words in Devanagari, which is worse than before for our main case.
- **Auto-detect, then retry once as Urdu if any Devanagari came back.**
- **Always ask the user for the language.** Too much friction per meeting.

## Decision

- `/transcribe` and `/summarize` (with `audio_key`) take an optional `language`: `auto` (default),
  `ur` or `en`. The ML service defaults to `auto` too.
- With `auto`, the engine detects the language. If the result contains Devanagari, the same audio is
  sent again with `language=ur`, and that result is used. English and plain Urdu keep their first
  result, so only Urdu-English clips pay for a second request.
- The mixed Urdu-English prompt (ADR-0023) is sent for `ur` and `auto`, and left out for `en`.
- The Devanagari warning stays. If the retry still returns Devanagari, the warning is reported.

## Consequences

- Measured on four clips (docs/evaluation/recordings_run/language_fix.md): English stays English,
  the mixed and overlapping clips return Urdu script again, Urdu is unchanged.
- A mixed clip costs two provider requests, so it uses twice the free-tier quota.
- A clip that is truly Hindi would be forced into Urdu. Out of scope for this product.
- ADR-0023's "Urdu requests pass `language=ur`" now applies only when a caller asks for `ur`.
