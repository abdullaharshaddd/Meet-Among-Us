# Language fix: results before and after (ADR-0027)

The same four clips (`Recordings/`, run through `POST /workspaces/{id}/transcribe` on 2026-11-13,
Groq `whisper-large-v3`, workspace "Speaker ID Test"). Entries come from the backend, so the
`language` column is the script of each entry's text.

| Clip | Before: forced `ur` | Auto-detect only | Auto-detect, retry as Urdu on Devanagari (final) |
|---|---|---|---|
| English | **Wrong.** Phonetic Urdu script, e.g. "ہی عبداللہ، فائیپ میٹنگ…". Entries: 10 `ur`, 1 `mixed`. | Engine says English. "Hi Abdullah, let's start the FIB meeting…". 11 `en`. | Same as auto: English, 11 `en`, no warning. |
| Bilingual | Good. Urdu script with English terms in Latin. 14 `mixed`. | **Broke.** Engine says Hindi. 119 words in Devanagari ("शुरू करते हैं"). 10 `en`, 5 `unknown`. | Good again. Engine says Urdu. 14 `mixed`, no warning. |
| Urdu | Good. 13 `ur`. | Good, identical. | Good, identical. |
| Bi-overlapping | Usable. 12 `mixed`, 2 `ur`. | **Broke.** Engine says Hindi. 117 Devanagari words. | Good again. 14 `mixed`, no warning. |

## What this shows

- The reported problem is fixed: English audio now comes back in English.
- Auto-detect alone made the main use case worse. Whisper hears Urdu mixed with English and calls
  it Hindi. That is why the retry exists (not in the original request, added after this result).
- The retry costs one extra provider request on the two mixed clips only. Transcribe time stayed
  about the same (31–42 s per clip, mostly speaker identification and the first request).
- The prompt (mixed Urdu-English) is sent with `auto`. English stayed English with it, so it does
  not drag English into Urdu on this clip. One clip is not proof for all English.

## Still wrong

- Speech-recognition errors remain in every language: "ElevenLabs Scribe" is heard as "11 laps
  scribe" or "GrokWhisper", "Groq" as "croc" or "grok". The summary repeats them.
- The Devanagari warning is kept and was empty in the final run on all four clips.
- Not measured: word error rate. These clips have no reference transcripts.
