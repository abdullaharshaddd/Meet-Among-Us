# Evaluating the summarizer

The prompted baseline (ADR-0025, ADR-0026) is scored on three things, so the fine-tuned model can be
compared with the same measures later. None of the scored measures below has been run yet. A first
look at the four development clips, before and after two fixes, is in
[recordings_run/](recordings_run/README.md).

## Test set

- The four clips in `Recordings/` (English, Urdu, Bilingual, Bi-overlapping; 80–120 s) are for
  development only. They are too short to hold real decisions, and a score over four items is noise.
- Test set: **at least 10 meeting-style clips of 3–8 minutes, each with 2 independent hand-written
  reference summaries (20 references).** 20 clips with 2 references each (40) is better.
- Two references per clip steadies ROUGE/BERTScore, and the score between the two humans is the
  ceiling the model is compared against.
- Report means with bootstrap confidence intervals.
- **Never train the fine-tuned model on the test clips.** The comparison is invalid if you do.

## 1. Groundedness (human judged)

For each claim (summary sentence, key point, decision, action item), a judge reads every cited
turn and marks it *supports*, *partly* or *does not support*.

- **Citation precision** — cited turns that support their claim, over all cited turns.
- **Supported-claim rate** — claims with at least one supporting turn, over all claims.
- **Unsupported-claim rate** — the made-up rate. Report it first.
- Two annotators judge about 25% of the claims. Report Cohen's kappa to show the labels are reliable.
- Free automatic proxy: the share of decisions and action items with no warning (quote found in
  the cited turns). It is a floor on trust, not a replacement for the human judgement.

## 2. Decisions and action items

Each clip gets a hand-written gold list: task, owner, deadline for action items, and decision and
who proposed it for decisions. Match predictions to gold by hand, then report:

- precision, recall and F1 of items found;
- **owner accuracy** on matched action items;
- deadline exact-match, and `decided_by` accuracy.

## 3. ROUGE and BERTScore against the references

- ROUGE-1, ROUGE-2 and ROUGE-L between the generated summary and each reference; take the better of
  the two references per clip.
- BERTScore with a multilingual model (`xlm-roberta-large`, with baseline rescaling), because names
  and quotes keep Urdu script.
- Both run in the `ml` environment (torch is already there). The script is written once the
  references exist.
- ROUGE rewards matching words, so it will undersell a summary that is right but worded differently.
  Read it next to groundedness, never alone.

## Running the models

Each clip is summarized once per engine (`groq`, `gemini`) with the same transcript. Record the
engine, model id, attempts (1 or 2) and warnings. The free daily caps are small (see ADR-0025), so
batch the runs.

## First look: the four development clips (2026-11-13)

Not a score, a four-clip check. Details and caveats in `recordings_run/`.

- **Speaker identification failed** on these clips: 0 of 55 turns named. See
  `recordings_run/identify_scores.md` and `channel_check.md`.
- **Language fix (ADR-0027):** English audio no longer comes back as Urdu script. Auto-detect alone
  broke the mixed clips (Hindi script), so it retries as Urdu when Devanagari appears.
  See `recordings_run/language_fix.md`.
- **Stricter decisions and action items (ADR-0026 update):** items need an explicit statement, a
  quote that is in the cited turns, and an unnamed owner reads "owner not identified". Over 12
  summaries the quote check dropped 3 decisions and 2 action items. Some items that look invented are
  faithful to a wrong transcript, so they remain. See `recordings_run/summarizer_fix.md`.
- Each summary needs the Groq key only. Gemini has still not been run (no `GEMINI_API_KEY`).
- One more number to collect in the real evaluation: the **dropped** count per clip. It is a free
  signal of how often the model writes something the transcript does not back.
