# 0006 — Audio level meter renders scrolling history, not instantaneous level

## Context

The app's differentiator is voice, and the level indicator is the one component the brief calls
out as worth real design effort, reused in Phase 4 enrollment and later in meeting recording. It
needs to answer a real question in each context: during a 30-second enrollment take, "is my mic
actually picking me up"; during a 2-hour meeting with the phone face-down on a table, "has it
been capturing this whole time." A single bar answers neither — it only shows the current
instant, so a glance during a pause between sentences looks identical to a glance at a dead mic.

A first pass (thick flex-width bars, hue switching between grey/teal/amber, a decaying peak-hold
hairline, per-bar `withTiming` smoothing) was reviewed and rejected: at that bar width and count
it read as a bar chart, not a waveform, and coloring roughly half the meter amber made "clipping"
look like a permanent broken state instead of a rare one. The revision below is what's actually
implemented.

## Options considered

- **Single bar / VU-style meter** — simplest, matches most consumer apps, but is a poor fit:
  it can't distinguish "silent right now" from "not capturing at all," which is exactly the
  failure this component exists to catch.
- **Circular / orb-style visualizer** — visually distinctive but decorative, and the brief's
  direction (Linear/Vercel/Raycast — restrained, engineered) explicitly rules out ornament for
  its own sake.
- **Scrolling amplitude history on a fixed grid of hairline bars**, newest sample entering from
  one edge, mirrored around a center line — reads as instrument tape / a seismograph trace,
  answers "has it been capturing" at a glance, and the mirrored form is the universal audio read
  (no legend needed).

## Decision

Scrolling history, as hairline bars: 2px wide, 2px gap, ~40-60 of them depending on the
container's measured width (`onLayout`, not a fixed count prop). Bar *positions* never move — a
single Reanimated shared value holds a ring buffer of recent samples, a write cursor advances
each tick, and bar *i*'s content is `buffer[(cursor + i) % N]`. The "scroll" is an illusion
produced by which sample each fixed position currently displays.

**All bars are accent teal; amplitude is opacity, not hue** — 25% at the floor, 100% at full
loudness — so the tape reads as one continuous signal rather than switching colors block to
block. The one exception is clipping: a bar at or above the enrollment quality gate's clip
threshold (matching `enrollment_samples.rejection_reason` in DATA_MODEL.md) gets a 2px amber
tick capping just that bar, not a hue change on the bar itself — clipping is rare, so it should
look like an alert, not a recoloring of the meter. There is no peak-hold hairline in this
revision; it added visual complexity the opacity encoding doesn't need.

Height and opacity are set directly per tick — **no `withTiming`/`withSpring`, no stagger**. A
hard cut to the new sample every step is what makes this read as a seismograph rather than a
bouncing bar chart. The tick itself is capped at 30fps via `useFrameCallback`'s
`timeSincePreviousFrame`, entirely on the UI thread, and fully stopped (`setActive(false)`)
whenever the meter isn't capturing — not just cheap per-frame, actually not running.

Reduced motion doesn't fall back to a slower version of the same animation — it seeds the ring
buffer once with a fixed, deterministic waveform shape and never advances it, so a
motion-sensitive user still sees "audio is active" without any animation running.

## Consequences

- No SVG or Skia dependency — plain `View`s driven by Reanimated, which was already installed.
- The component takes `level: number` (0..1) as a plain prop, bridged into a shared value by one
  effect; from there, everything (the 30fps tick, the ring buffer, every bar's style) runs in
  worklets and never re-renders React. The ceiling that matters now is how often the *caller*
  updates the `level` prop, not the render cost of the meter itself.
- The component has no opinion on where samples come from; wiring a real mic callback is Phase 4
  (enrollment) / Milestone 2 (recording) scope, not this task's.
