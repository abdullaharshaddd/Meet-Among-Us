# 0026 — Grounding every claim with turn citations

## Context

A summary is only useful if a person can check it. The rule is that nothing may be stated that is
not in the transcript, and every decision and action item must point at the turns it came from.

## Options considered

- **Ask for timestamps.** Models garble numbers like "01:42", and a wrong time looks like a real one.
- **Verify with a second model call.** Doubles the cost against small free daily limits.
- **Number the turns and cite the numbers.** The model sees `[3] (01:42) Abdullah: …` and cites `3`.
  The backend turns each number back into a start time and speaker.

## Decision

- Turns are numbered from 1 and cited by number. A cited number that does not exist is a **hard**
  failure.
- Every decision and action item carries a `quote`, copied word for word in its original script
  (Urdu stays Urdu), which can be string-checked against the cited turns.
- **Hard checks** (reply is not JSON, wrong shape, an item with no turns, an unknown turn number,
  a summary outside 1–8 sentences) cause **one retry** with the reasons appended to the prompt.
  A second failure returns a clear 502 listing the reasons.
- **Soft checks** only add a warning to the item, shown on the dev page: the quote is not found in
  the cited turns, the owner or `decided_by` is neither a speaker nor in the cited text (or is
  "Unclear"), or the deadline is not in the cited text. These are warnings because an Urdu spelling
  variant should not burn a retry from the daily quota, and the warning rate doubles as a free
  groundedness measure.
- The summary asks for 5–8 sentences but accepts fewer. Our test clips are about two minutes long,
  and forcing five sentences from them invites invented content.
- Output language is English, with names, terms and quotes kept as spoken.
- "Unknown Speaker N" and "Unclear" are labels, never guests.

## Consequences

- Citations prove where a claim came from, not that the turn supports it. That is measured
  by hand (docs/evaluation/summarization.md).
- Quotes are normalised (case, punctuation) before comparing, but a transcript spelling the same Urdu
  word two ways will still raise a warning.

## Update 2026-11-13: what is dropped, and what is only warned

The four-clip run showed decisions and action items that nobody had stated (a status update read
as a decision, a task filled in from "as discussed"). Changes:

- **Prompt:** only items explicitly said. A decision needs words showing it was settled, an action
  item needs someone taking the task in so many words, and an empty list is a correct answer.
- **Dropped, not warned:** a decision or action item whose quote is not in the turns it cites. The
  response reports `dropped_decisions` and `dropped_action_items`.
- **Deadline not in the cited turns:** the deadline is removed and a warning says so.
- **Owner that is "Unknown Speaker N" or "Unclear":** shown as "owner not identified". The same
  rule applies to `decided_by`, which then reads "speaker not identified".
- Dropping does not trigger the retry. A retry costs quota and the next reply can fail the same way.

The quote check proves the words exist in the transcript, not that they mean a decision, and it
cannot see a speech-recognition mistake. See docs/evaluation/recordings_run/summarizer_fix.md.
