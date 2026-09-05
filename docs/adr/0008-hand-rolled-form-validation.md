# 0008 — Hand-rolled inline validation, no form library

## Context

Login and signup each need 2–3 fields validated as the user types, not only on submit. This is
the first form validation in the app, and whatever pattern it establishes is what enrollment and
project-creation forms will copy later — worth deciding deliberately once.

## Options considered

- **A form library** (`react-hook-form`, Formik) — handles validation timing, error state, and
  submit-blocking for you, and scales well to large/complex forms with cross-field rules.
- **Hand-rolled**: a small `useValidatedField(validate)` hook per field, showing the error only
  after the field's first blur so a blank field doesn't show "required" before anyone's typed
  anything.

## Decision

Hand-rolled. Two forms with three plain fields each and no cross-field rules (nothing here needs
"confirm password" or conditional fields) is not enough surface to justify a dependency whose
main value is managing complexity these forms don't have. `useValidatedField` in
`src/hooks/useValidatedField.ts` is ~15 lines and used identically by both screens.

## Consequences

- One less dependency, and one less library's API for three student developers to learn.
- If a later form needs cross-field validation, async validation (e.g. "is this email already
  taken" as you type), or gets large enough that per-field `useState` calls become unwieldy,
  that's the signal to introduce a form library — not before.
- The pattern (`useValidatedField` + a small `validators` map) is what Phase 4's enrollment form
  and Phase 5's project-creation form should reuse, not reinvent.
