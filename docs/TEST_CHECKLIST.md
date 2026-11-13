# Test checklist: the connected flow

Written 2026-11-13 for the branch `feature/connected-flow`. You test the screens by hand; this says what to start,
what to click, and what you should see.

**The 12 steps are my own grouping** of the flow from sign-up to account deletion. Change them if your team counts
differently.

**Legend**
- **Tests** = covered by backend tests against the test database (no screen involved).
- **Real run** = I ran it against the real Groq, R2 and ML service through the API, no screen.
- **Browser (partial)** = a headless browser on Expo web drove that screen once, for part of the step.
- **Not checked** = the screen was written and type-checked (`tsc --noEmit`) but nobody has clicked it.

No screen in this list has been checked on an Android device.

---

## 0. Start the three services

Three terminals, from the repo root. Stop each with Ctrl+C.

```bash
# 1. Backend API on 8003
cd backend && uv run uvicorn app.main:app --port 8003

# 2. ML service on 8500 (it needs ml/.env, so pass --env-file)
cd ml && uv run --env-file .env uvicorn ml.service:app --port 8500

# 3. Mobile app on Expo web, 8081 (phone-width browser window is best)
cd mobile && npx expo start --web --port 8081
```

Check before you start:
- `http://localhost:8003/health` shows `{"status":"ok","db":"ok"}`.
- `http://localhost:8500/version` shows `"api_version":2`. If the backend log warns about the ML version at start-up,
  restart the ML service.
- The first Expo web load takes a minute or two while it bundles.

For a phone or an emulator you need a development build (`npx expo start --dev-client`), which is not built yet.

Use two browser profiles (or one normal and one private window) so you can be two people at once. Below, **Olive**
owns the workspace and **Max** is a member.

---

## 1. Sign up and log in
1. Sign up Olive with an email and a password. Sign up Max in the other window.
2. Log out and log in again.

**You should see:** the Meetings tab after login, with "No meetings yet", a "Set up your voice" card and two
"New meeting" buttons. A wrong password shows an error and does not log in.

Verified: Tests (auth). Browser (partial): Olive logging in and seeing the empty Meetings list.

## 2. Create a workspace
Olive: switcher at the top, create a workspace, give it a name.

**You should see:** the workspace name at the top of the Meetings tab.

Verified: Tests. Not checked in a browser (the test run created the workspace through the API).

## 3. Join the workspace
- **By code:** Olive opens Invite and reads the join code. Max opens Settings, chooses "Join with a code", types it.
- **By email:** Olive enters Max's email on Invite and sends. Max pastes the personal invite code from the email into
  the personal invite code field on the same screen. See "Real invite email" below for the email itself.

**You should see:** Max sees Olive's workspace. Olive's Members screen lists both people. The invite email leads with
the join code and the steps, with the link second. While `INVITE_LINK_BASE_URL` is `http://localhost:8003`, the link
only opens on the host computer, and the email says so.

Verified: Tests (invites, members, the email wording). Not checked: the Invite and Join screens, the `/join/{token}`
landing page, and a real email arriving (see below).

## 4. Enroll your voice
Each person: "Start enrollment", read the three passages.

**You should see:** "0 of 3" counting up to done. Enrolled people can be named in meetings automatically.

Verified: this predates the connected flow. Enrollment itself has tests and was used earlier, but speaker
identification names nobody on the team's `Recordings/` clips yet (the match floor of 0.72 is not reached), so expect
"Unknown Speaker N" in transcripts until that is fixed.

## 5. Create a meeting
Olive: Meetings, "New meeting", enter a title, tick Max, add a guest called Imran, "Create meeting".

**You should see:** Max's name next to his checkbox, and a meeting screen titled with your title, status "Waiting for
audio", a People list (Olive host, Max, Imran as Guest) and a heads-up if someone has not enrolled their voice. A
user who has not enrolled can still create a meeting.

Verified: Tests. Browser (partial): this screen was driven once; the missing member names that run found are fixed.

## 6. Consent
- Olive: "Review and agree", read the notice, "I agree to be recorded". Then tick "Imran agrees to be recorded"
  (only after Imran has told you he agrees).
- Max, in his window: open the meeting from his list, "Review and agree", "I agree to be recorded".

**You should see:** "You agreed." The meeting says who it is still waiting for until everyone has agreed. Asking for
an upload URL (or finishing an upload) before everyone has agreed is refused with a 409 that names who is missing,
before anything is stored.

Verified: Tests, including consent before upload. Browser (partial): the owner, guest and member consent screens.

## 7. Record the meeting
The recorder is Vaniya's part and does not exist yet. "Record the meeting" opens a screen that says "Recording is
being built".

Until it exists, attach audio yourself, same endpoints the recorder will call (see
`docs/handoff/recording-upload.md`). Everyone must have agreed first.

```bash
# backend and ML service running. MEETING_ID is the last part of the meeting page's address.
cd backend && uv run python ../scripts/attach_audio_to_meeting.py MEETING_ID path/to/audio.m4a
```

It accepts `.m4a`, `.flac`, `.wav`, `.webm` and `.ogg`, uploads, starts processing and waits until the meeting is
done or failed. It mints a token for the meeting's host from your local `backend/.env`, so it only works on this
machine.

**You should see:** the script prints the status changing to "Done."

Verified: Real run (an English `.ogg` reached done in 51 s). Tests. The placeholder screen is Not checked.

## 8. Processing status
Watch the meeting screen while the script runs, or reload it.

**You should see:** the status moves from waiting for audio to processing to done. If it fails, the screen gives a
readable reason and a retry that redoes only the missing step. The limits are 30 minutes and 150 MB.

Verified: Tests (success, each failure, retry, restart recovery, limits). Not checked on screen.

## 9. Read the result
Open the meeting once it is done and go through the tabs: Summary, Transcript, Decisions, Action items.

**You should see:**
- a short summary, plus key points;
- the transcript by speaker, with "Unknown Speaker N" for anyone who was not matched (a label, never a person);
- decisions and action items that each cite a turn. An item whose quote is not in the cited turns is dropped, so the
  lists may be short. Owners show "owner not identified" when nobody is named.

Verified: Real run (summary, citations and "not identified" labels, via the API). Tests. Not checked: the tabs.

## 10. Rename an unknown speaker
Transcript tab, tap "Unknown Speaker 1", choose Max (or add a guest).

**You should see:** every line from that speaker changes to the new name, in the whole meeting. You can undo it.
People who are not in the meeting cannot rename.

Verified: Tests. Not checked on screen.

## 11. Tasks
Tasks tab: action items from your meetings. Tick one, untick it.

**You should see:** "Open · N" and "Done · N" counts change. You never see items from meetings you are not in.

Verified: Tests. Not checked on screen.

## 12. Members, roles and account deletion
- Olive: Members. Make Max an admin; remove someone; transfer ownership.
- Max: Settings, Delete account. Read what goes and what stays. Try a wrong password, then the right one.

**You should see:**
- roles change on the Members screen. Someone who owns a workspace with other people cannot delete their account and
  is told to hand it over first;
- a wrong password shows "That password is not right.";
- after deletion Max is signed out and cannot log in. In Olive's meeting his name now reads **Former member**, his
  words stay without his name, and his consent answer stays.

Verified: Tests (member management, deletion, anonymisation). Not checked: both screens, and Google re-authentication
for accounts that signed up with Google.

---

## Real invite email
Not yet sent. Set up and ready: all seven SMTP and invite variables are filled in `backend/.env`. To try it, send an
invite from the Invite screen to an address you control, then check the inbox and the spam folder, and tell the team
whether it arrived and where it landed.

## Clean up
- Ctrl+C each of the three terminals.
- Test accounts pile up in the dev database. To clear it (it deletes everything in the dev database and its R2
  bucket): `cd backend && uv run python ../scripts/reset_dev_data.py --confirm`. It refuses against the test project
  and without `DEV_TOOLS_ENABLED=true`.

## Not covered by any of this
Recording in the app (Vaniya), projects, the assistant (says "Coming soon"), the Android build, and the 20-minute
`.mp4`. Gemini has never run.
