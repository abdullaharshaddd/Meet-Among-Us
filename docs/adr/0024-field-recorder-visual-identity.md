# 0024 — "Field Recorder" visual identity: Instrument fonts, Paper and Studio palettes

## Context

ADR-0005 chose IBM Plex and ADR-0022 chose a teal-on-charcoal palette. Both read as neutral and
corporate, and the app had no identity of its own. The product is a recorder that sits on a
table in a room full of people, so the interface should feel like a piece of audio hardware
(Teenage Engineering TP-7: monochrome, mono labels, hairline rules, one signal colour) rather
than a SaaS dashboard. Reading screens (summary, transcript) borrow Granola's warm paper canvas
and serif headlines.

## Options considered

- **Keep Plex and teal, tune them** — cheap, but the problem was identity, not tuning.
- **Dark-only recorder look** — strongest hardware feel, but long transcripts are read in
  daylight and ADR-0022 already committed to light and dark.
- **Paper and Studio themes with one orange signal colour** — keeps both themes, and gives the
  colour a single job.

## Decision

- Palettes named Paper (light) and Studio (dark), warm neutrals, ink-filled primary buttons.
- Orange `signal` means recording, live, and the record button only. It is never used for links,
  tabs, selection or ordinary primary buttons.
- Instrument Serif (24 pt and up, display only), Instrument Sans (UI), Geist Mono (labels,
  numbers, timers). All SIL OFL on Google Fonts, JS and asset only, so no native rebuild.
  Noto Nastaliq Urdu stays. Urdu is never set in the Instrument fonts, and Latin never in Nastaliq.
- Six speaker hues for non-text marks only, picked by a stable hash of the speaker or guest id.
- Cards are flat with a hairline border. Only floating things get a shadow.
- Theme mechanics from ADR-0022 (system-driven, in-app override) are unchanged.

## Consequences

- Supersedes ADR-0005 and the palette part of ADR-0022. ADR-0006 (meter) and ADR-0007 (bidi)
  are amended when the meter and `BilingualText` are rebuilt.
- Paper `textTertiary` on `sunken` is 4.38:1, below 4.5. Text on `sunken` uses `textSecondary`.
- `signal` on Paper canvas is 2.92:1 as a non-text mark, just under 3:1. It is always paired
  with a text label, so recording state never relies on colour alone.
- A temporary `theme/legacy.ts` keeps unmigrated screens running and is deleted with the old
  `components/` folder.
