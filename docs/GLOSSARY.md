# Glossary

Plain-English definitions, added the first time each term is used in code.

- **Connection pooler** — a proxy that sits in front of Postgres and hands out a small set of
  real database connections to many client requests, so the database itself doesn't have to
  open a connection per request.
- **Transaction pooling mode** — a pooler mode that hands out a database connection only for
  the length of one transaction, then takes it back — cheaper, but the connection you get can
  change between transactions.
- **Migration** — a versioned, scripted change to the database schema (e.g. "add this table"),
  so every environment ends up with the same schema by applying the same scripts in order.
- **Design token** — a named constant (a color, font, spacing value) used instead of a
  hardcoded literal, so the whole app can be restyled by editing one file.
- **Google ID token** — a signed JWT from Google that proves who a user is (their Google
  account, email, name) — different from a Google *access* token, which grants permission to
  call a Google API on the user's behalf. Sign-in only needs the ID token.
- **JWT access/refresh token pair** — a short-lived access token (sent with every request,
  ~15 min) and a long-lived refresh token (~30 days, used only to get a new access token).
  Splitting them means a leaked access token expires fast, while the user doesn't have to
  log in again constantly.
- **RMS level** — a rolling average of how loud an audio signal is over a short window, the
  standard way to turn a raw waveform into the single "how loud right now" number a level
  meter displays.
- **Clipping** — when an audio signal is louder than a microphone or file format can represent,
  so its peaks get flattened off instead of recorded accurately — permanent, unrecoverable
  distortion, not something you can fix after the fact.
- **Peak hold** — a level meter convention where the loudest recent point stays marked (and
  slowly decays) after the sound itself has quieted down, so a glance shows recent headroom,
  not just the current instant.
- **Ring buffer** — a fixed-size array that wraps around: writing past the last slot continues
  at slot zero. Lets you keep a rolling window of recent history without ever resizing or
  shifting an array.
- **RTL (right-to-left)** — a script, like Urdu or Arabic, that reads and lays text out from
  right to left instead of left to right.
- **Bidirectional isolate** — a pair of invisible Unicode characters placed around a run of
  text in one direction (e.g. Urdu) to stop it from disturbing the layout of surrounding text
  going the other direction (e.g. English) when the two are mixed in one sentence.
- **Type scale** — a fixed, named set of font sizes and line-heights (e.g. "heading", "body",
  "caption") that every screen picks from, instead of choosing arbitrary numbers per screen.
- **Elevation** — how "raised" a surface looks relative to the screen behind it (e.g. a card vs.
  a modal on top of it), signalled here by background color and border rather than a drop shadow.
- **Reduced motion** — an OS-level accessibility setting a user turns on to minimize animation;
  respecting apps switch springs/transitions for instant state changes when it's on.
- **Keystore** — a file holding the cryptographic key an Android app is signed with. Google
  Sign-In (and the Play Store later) identify *which* build of an app is asking by the
  certificate in its keystore, not just its package name.
- **SHA-1 fingerprint** — a short hash of the certificate inside a keystore. Google Cloud
  Console uses it to recognize "this specific signed build is really MeetAmongUs," which is why
  a new keystore (e.g. a new EAS build profile) needs its fingerprint registered again.
- **Salt** — a random value mixed into a password before hashing, unique per user, so two
  people with the same password get different stored hashes and an attacker can't precompute
  one lookup table that cracks every account at once.
- **Key derivation function (KDF)** — a hash function deliberately made slow and memory-hungry
  (like scrypt), so that guessing millions of passwords against a stolen hash takes
  impractically long, unlike a fast general-purpose hash like SHA-256.
- **Timing-safe comparison** — comparing two secrets byte-by-byte in constant time regardless of
  where they first differ, so an attacker can't use response-time differences to guess a secret
  one byte at a time.
- **`jti`** — "JWT ID," a standard JWT claim holding a unique identifier for that one token.
  Used here to look up the token's row in the database, since the token itself can't be revoked
  once issued but the database row backing it can be marked used.
- **Refresh token rotation** — issuing a brand-new refresh token every time the old one is
  redeemed, and invalidating the old one, so a single refresh token is only ever usable once.
- **Token family** — every refresh token produced by rotating from one original login, linked so
  that if an already-used one is ever presented again (a sign it was stolen and replayed), the
  whole chain can be shut down at once instead of just the one token.
- **Sliding window (rate limiting)** — counting only the requests from the last N seconds
  (dropping older ones as time passes) rather than resetting a count at fixed clock intervals,
  so the limit applies evenly no matter when in a minute a burst happens to land.
- **UI thread vs. JS thread** — React Native runs app logic (state, re-renders) on one thread and
  actual on-screen drawing on another. Animation code that only touches the UI thread (as
  Reanimated's `useFrameCallback`/`useAnimatedStyle` do) keeps running smoothly even if the JS
  thread is busy or the component isn't re-rendering at all.
