> **Status: partly superseded by [ADR-0024](0024-field-recorder-visual-identity.md).** The two-theme mechanics (system-driven, in-app override) still apply. The teal palette and accent do not.

# 0022 — Light and dark themes, retuned palette

## Context

CLAUDE.md and PROJECT_BRIEF §6 locked "dark mode only", canvas `#0D1117`, accent `#14B8A6`.
Those values are GitHub's dark theme plus Tailwind's teal-500, so the app looked borrowed. The
redesign also asks for light mode, and `app.json` already sets `userInterfaceStyle: "automatic"`.
The old teal is about 2.5:1 on white, so it cannot carry text or buttons in a light theme.

## Options considered

- **Keep dark only, restyle it** — smallest change, but people who use the app in daylight or
  have a light system theme get a dark app regardless.
- **One palette, light values derived by inversion** — fast, but the accent fails contrast and
  shadows look wrong.
- **Two hand-tuned palettes behind one token shape** — more values to maintain, but each theme
  is checked for contrast on its own.

## Decision

Two palettes (`light`, `dark`) with the same shape in `mobile/src/theme/tokens.ts`. A
`ThemeProvider` picks one from the system setting; dark is the fallback when the phone doesn't
say. Neutrals lean slightly teal so surfaces and accent feel like one family. The accent is
`#2DD4BF` in dark and `#0F766E` in light. Danger and recording stay one red hue; filled
destructive buttons use a darker red than red text does. Fonts stay IBM Plex (ADR-0005).

## Consequences

- Components read colors with `useTheme()`, not a static import. The static `colors` export
  is a temporary dark-only alias for components not yet migrated.
- Dark mode builds depth from lighter surfaces and hairlines; light mode uses soft tinted shadows.
- Every new color is added to both palettes or neither. A change to one theme is a review flag.
- CLAUDE.md and PROJECT_BRIEF §6 are updated to match.
