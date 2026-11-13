# 0025 — Summarization: Groq as the default, Gemini as the comparison

## Context

FYP-1 ends at summarization. This is the prompted baseline: a free LLM with a good prompt and no
fine-tuning, so a fine-tuned model can be compared against it later. The transcript mixes Urdu and
English, and it has to fit in one request.

## Options considered

Free limits below come from 2026 third-party write-ups, not the providers' own pages. They change
without notice, so check the Groq console and aistudio.google.com/rate-limit before relying on them.

| Option | Free limits (approx.) | Notes |
|---|---|---|
| Groq `openai/gpt-oss-120b` | 30 req/min, 1,000 req/day, 8K tokens/min, 200K tokens/day | Open weights, key already set up. The 8K tokens/min cap means about 5–8 minutes of Urdu-English per request. |
| Gemini Flash-Lite | 10 req/min, 500 req/day, 250K tokens/min | Long context, so a whole meeting fits. Needs a new key. Closed model. |
| Cerebras | One-time $5 trial credit, 5 req/min | No permanent free tier any more. Ruled out. |

## Decision

- **Groq `openai/gpt-oss-120b` is the default.** It is open-weight, like the Whisper choice in
  ADR-0023, so it can be fine-tuned or replaced by a model we tune.
- **Gemini Flash-Lite is the comparison**, mainly because it takes long transcripts.
- Both speak the OpenAI chat-completions format, so one `ChatSummarizer` class is configured twice.
  A different provider is one more line in `build_summarizer`.
- The call lives in the ML service next to the transcribers, so keys stay in `ml/.env`. The backend
  is a key-free HTTP client, as it is for transcription.
- Model ids come from `GROQ_SUMMARY_MODEL` and `GEMINI_SUMMARY_MODEL`, because free catalogs change.
- **Single pass only.** A transcript the provider refuses as too large returns a clear 413 that
  suggests the other engine. Split-then-merge is needed once real meetings (up to 2 h) arrive.

## Consequences

- Groq's free cap limits the demo to short meetings. Gemini is the fallback.
- The daily caps are small. Evaluation runs must be batched and counted.
- Two providers means two sets of rate-limit behaviour. The shared retry helper handles both.
