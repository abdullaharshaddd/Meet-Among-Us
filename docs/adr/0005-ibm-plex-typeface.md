# 0005 — IBM Plex Sans replaces General Sans as the UI typeface

## Context

CLAUDE.md and PROJECT_BRIEF.md §6 both lock "General Sans (or Satoshi) for display, IBM Plex
Mono for numerics/timestamps." Neither font is a Google Font: General Sans ships from Fontshare
as hand-vendored `.otf` files with no Expo package, which is why `tokens.ts` had it as a comment
("loaded manually") with no actual font ever added to the repo. The Task 1 brief explicitly
specifies IBM Plex Sans for UI text instead, overriding both docs.

## Options considered

- **Keep General Sans** — matches the original docs, but means downloading and committing
  `.otf` binaries, wiring a manual `expo-font` load, and maintaining a font with no
  `@expo-google-fonts` package the moment a new weight is needed.
- **IBM Plex Sans, matching the mono face already locked in** — one type family (Sans + Mono
  are drawn as a matched pair by IBM) instead of two unrelated ones, and it installs the same
  way as the mono and Urdu faces already in use: `@expo-google-fonts/*`, no binaries in the repo.

## Decision

IBM Plex Sans for UI text (regular/medium/semibold), IBM Plex Mono for numerics and timestamps,
Noto Nastaliq Urdu for Urdu — all three via `@expo-google-fonts`. CLAUDE.md and
PROJECT_BRIEF.md §6 are updated to match.

## Consequences

- One less bespoke asset pipeline: every font in the app now loads the same way
  (`useFonts` from an `@expo-google-fonts` package), so there's one pattern to maintain, not two.
- Sans and mono share x-height and stroke weight by design, which a General Sans + IBM Plex Mono
  pairing did not guarantee.
- If a future reviewer asks why the docs don't match the code, this ADR is the answer — not a
  drift to quietly fix later.
