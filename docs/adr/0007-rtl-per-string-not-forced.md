# 0007 — Per-string RTL via writing direction and Unicode isolates, not `I18nManager.forceRTL`

## Context

The app is bilingual: Urdu text appears inside otherwise English, left-to-right screens (a
button label, a project name, a transcript line later) rather than the whole app switching
direction. React Native's usual RTL mechanism, `I18nManager.forceRTL(true)`, mirrors the entire
layout tree — navigation direction, icon placement, every screen — and requires an app restart
to take effect. That's the correct tool for a fully-Urdu app; it's the wrong tool here and, once
screens are built against a forced-RTL layout, expensive to undo.

## Options considered

- **`I18nManager.forceRTL`** — flips everything, one-way, restart required. Wrong shape for a
  mixed-language UI where most chrome stays LTR.
- **Per-string direction** — an Urdu run gets `writingDirection: 'rtl'` and `textAlign: 'right'`
  applied only to that `Text` node, leaving the surrounding layout untouched.

## Decision

A dedicated `<Urdu>` text component (`src/components/Text.tsx`) sets the Nastaliq font,
`writingDirection: 'rtl'`, `textAlign: 'right'`, and a line-height ratio (~2.1x) wide enough for
Nastaliq's tall ascenders/descenders, which clip under a Latin line-height on Android.

Urdu content is additionally wrapped in Unicode directional isolates — U+2068 (FSI) before,
U+2069 (PDI) after. React Native has no equivalent of CSS `unicode-bidi: isolate`, so without
this an Urdu run embedded mid-English-sentence can drag neighbouring LTR punctuation into the
wrong visual position. The isolate characters tell the Unicode bidi algorithm "this run is a
sealed unit," which is exactly what embedding one language inside another needs.

## Consequences

- Every other component stays LTR with zero RTL-awareness; only `<Urdu>` carries the direction
  logic, in one place.
- Anyone writing a mixed-language string must use `<Urdu>` for the Urdu portion rather than one
  plain `<Text>` — a convention, not a compiler-enforced rule. Worth a lint rule later if it's
  ever gotten wrong in review.
- If a future milestone needs a fully Urdu-first surface, `forceRTL` is still the right tool
  there — this ADR doesn't rule it out, it just says today's mixed-language screens don't need it.
