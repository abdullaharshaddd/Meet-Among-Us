# Enrollment Passages

Three short passages a user reads aloud during voice enrollment — one per
`enrollment_samples.language` value (`en` / `ur` / `mixed`, see DATA_MODEL.md). Each is
sized for roughly 12 seconds at a natural, unhurried conversational pace — read it out loud
once to feel the timing; don't count syllables against a stopwatch. Full rationale for why
three passages in three languages is in `docs/adr/0012-three-passage-bilingual-enrollment.md`.

Content is deliberately mundane (tea, a walk, a work deadline) — nothing that reads as a
form, no names, no numbers, nothing personally identifying.

---

## 1. English

> Most mornings I like to take a slow walk before the city gets loud, just to clear my
> head and notice how the light changes along the way.

**Phonetic coverage:** plosives (p, t, k, b, d, g), fricatives (f, s, z, sh), nasals (m, n),
liquids (l, r), the full vowel spread from "most" to "city" to "way" — a natural sentence,
not a constructed pangram.

---

## 2. Urdu

> مجھے صبح کی چائے کے بغیر دن شروع ہی نہیں لگتا، چاہے کام کتنا بھی زیادہ ہو، تھوڑی دیر
> سکون سے بیٹھ کر چائے ضرور پیتا ہوں۔

**Transliteration:** Mujhe subah ki chai ke baghair din shuru hi nahi lagta, chahe kaam
kitna bhi zyada ho, thori der sukoon se baith kar chai zaroor peeta hoon.

**Meaning:** My day doesn't feel like it's started without morning tea — no matter how
much work there is, I make sure to sit calmly for a bit and have my tea.

**Phonetic coverage:** retroflex ڑ (thoṛi), aspirated consonants بھ / تھ (bhi, thori),
nasalisation ں (nahi, din), the guttural غ (baghair) and ض (zaroor) — sounds ECAPA-TDNN's
VoxCeleb training data essentially never saw.

---

## 3. Code-switched

> یار، deadline زیادہ دور نہیں، لیکن client سے requirements ابھی تک clear نہیں ہوئی، اس
> لیے میں پہلے ایک quick call schedule کرنا چاہتا ہوں تاکہ confusion نہ رہے۔

**Transliteration:** Yaar, deadline zyada door nahi, lekin client se requirements abhi tak
clear nahi huyi, is liye main pehle ek quick call schedule karna chahta hoon taakay
confusion na rahe.

**Meaning:** Look, the deadline isn't that far off, but the requirements from the client
still haven't been made clear, so I want to schedule a quick call first so there's no
confusion.

**Why this shape, not a translated sentence:** this is how the mixing actually happens in a
Pakistani office — English nouns for workplace concepts (*deadline*, *client*,
*requirements*, *quick call*, *confusion*) dropped straight into an Urdu grammatical frame,
with the Urdu verb doing the work around them (*clear nahi huyi*, *schedule karna chahta
hoon*). Nothing here is one language's sentence translated halfway into the other.

---

## Next step

Read all three aloud. Flag anything that feels stiff, too fast to read comfortably, or
unnatural for how you'd actually say it — these get baked into the enrollment flow once
approved, so this is the cheap point to fix them.
