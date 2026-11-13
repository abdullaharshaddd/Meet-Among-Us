# 0029 — Long transcripts: split into parts, summarize each, merge

## Context

Groq's free tier takes about 8,000 tokens a minute, and Urdu costs roughly one token per two characters. A
transcript over about 5 to 8 minutes of speech got a 413 and no summary. Meetings can run 30 minutes.
Every claim carries turn numbers (ADR-0026), so a method that renumbers turns would break the citations.

## Options considered

- **One request, fail on 413.** The state before. Long meetings get nothing.
- **Map, then reduce with a second model call** that writes one overall summary from the part summaries. Reads
  best, but doubles the calls on a tight per-minute budget, and the reduce step has to carry citations through
  a rewrite.
- **Split into parts, summarize each, merge without a model.** Simple, and citations survive because nothing is
  rewritten.

## Decision

- Cut the transcript between turns into parts of at most `summary_part_max_chars` (6000) characters. A single
  turn longer than that goes alone.
- Each part is summarized by the same `/summarize` call, with the turns keeping their numbers in the whole
  transcript. Citations therefore point at the right turn without any mapping.
- Merge in order: summary sentences follow each other, and key points, decisions and action items that two parts
  both report (same words, ignoring case and punctuation) are kept once. The counts of dropped items are added.
- If the provider still answers 413 for a part, that part is halved and each half retried. A single turn that is
  still too long fails.
- The result records how many parts were used (`parts`).

## Consequences

- A long meeting's summary reads as a run of per-part summaries (up to 8 sentences each), not one tight overview.
  A model-written overview is a later upgrade.
- A meeting costs one request per part. Groq's per-minute limit is handled by the retry wait (up to 30 s, three
  times), so a long meeting can take a few minutes.
- A decision split across a part boundary can be missed or reported twice. The overlap is not handled.
