# Summarizer fix: results before and after (ADR-0026 update)

Rule change: decisions and action items must be explicitly stated. Items whose quote is not in the
cited turns are dropped and counted. Owners that are "Unknown Speaker N" or "Unclear" read
"owner not identified". A deadline not in the cited turns is removed.

**How it was tested.** To separate this fix from the language fix, the *old* (forced-Urdu)
transcripts of `Urdu.ogg` and `Bi-overlapping.ogg` were re-summarized with the new rules, three
times each (Groq `openai/gpt-oss-120b`, temperature 0.2, so runs differ). Items are judged by
reading them against the transcript turns. Single runs per cell, so treat counts as indicative.

## Urdu.ogg

| | Before (4 decisions, 3 action items) | After (3 runs) |
|---|---|---|
| Decisions | Test both systems and compare errors. Use the free facility for now. **Schedule supervisor meeting Friday night at 2.** **Prepare a voice repository** (deadline next Wednesday). | Test both systems: 3 of 3. Free facility: 3 of 3. Schedule the supervisor meeting: **still 3 of 3.** The "voice repository" decision is **gone, 3 of 3** (it is a task, and now appears only as an action item). |
| Action items | Add people (owner "Unknown Speaker 3"), prepare audio repository, create "صحافے" (owners "Unknown Speaker 1/4") | Prepare audio repository: 3 of 3. Create "صحافے": 3 of 3. Add participants: 2 of 3. Owners now read "owner not identified". |
| Dropped by the quote check | n/a | 0, 0, 0 |

## Bi-overlapping.ogg

| | Before (2 decisions, 4 action items) | After (3 runs) |
|---|---|---|
| Decisions | Assign second engine to "Ladscribe". **Upgrade to pro tier.** | Second engine: 3 of 3. Upgrade to pro tier: **1 of 3.** One run also listed a content-free "decision final". |
| Action items | Comparison by Friday, workspace and invite flow, test-recording dataset, **prepare lights** | Workspace/invite flow, dataset, comparison by Friday: present. **"Prepare lights": still 3 of 3.** Owners "owner not identified". |
| Dropped by the quote check | n/a | 0/1, 0/0, 1/1 (decisions/actions) |

An earlier version of the prompt also produced "Adjust budget as discussed" (cites a turn that
states no task). The rule "the task itself must be in the cited turns, not completed from 'as
discussed'" was added and it did not reappear in the three runs.

## Full pipeline after both fixes (new transcript, default language)

| Clip | Decisions | Action items | Dropped (dec/act) | Attempts |
|---|---|---|---|---|
| English | 2 | 4 | 0/0 | 1 |
| Bilingual | 2 | 4 | 0/0 | 1 |
| Urdu | 2 | 2 | 0/0 | 1 |
| Bi-overlapping | 0 | 2 | 2/0 | 2 |

Across all 12 summarize calls in this phase the quote check dropped 3 decisions and 2 action items.
The prompt did most of the work; the check is a backstop.

## Verdict: not fully clean

- **Gone:** a task listed as a decision, "Adjust budget as discussed", and (in 2 of 3 runs) the
  pro-tier decision. Owners no longer show "Unknown Speaker N".
- **Remaining, and why:**
  - "Prepare lights" is what the transcript says. The speaker said "slides", the engine wrote
    "lights", and the summarizer cannot know. This is a transcription error, not an invention.
  - "Schedule supervisor meeting Friday night at 2": the speakers confirm that time in so many
    words ("جمعہ رات کو دو بجے"). The dialogue was meant to be Thursday 2 PM, so this is again a
    transcription error. Whether a confirmed meeting time is a "decision" is a judgement call. It
    would need a tighter rule (for example, require a decision word), and I have not added one.
- The quote check proves the words are in the transcript. It cannot tell a decision from a
  confirmation, or a heard word from a said word.
- Runs differ by one or two items each time. A real evaluation needs the 10+ clips in
  `docs/evaluation/summarization.md`.
