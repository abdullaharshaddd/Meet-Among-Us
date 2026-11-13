// Real end-to-end run in Expo web against the real backend. Heavy: it drives a headless browser, so it is not part of
// any test suite. Needs the backend (8003), the ML service (8500) and `npx expo start --web` (8081) running, and
// playwright from mobile/package.json. Run from mobile/:
//   node e2e/e2e_web.mjs [outputDir] [clip.wav]
// Screenshots and results go to outputDir (default e2e/out, git-ignored). It creates test accounts in the dev database.
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const SCRATCH = process.argv[2] ?? "e2e/out";
const CLIP = path.resolve(process.argv[3] ?? `${SCRATCH}/e2e_clip.wav`);
fs.mkdirSync(SCRATCH, { recursive: true });
const BASE = "http://localhost:8081";
const API = "http://localhost:8003";
const PASSWORD = "correct horse";
const stamp = Date.now().toString(36);
const results = [];
const shot = (name) => `${SCRATCH}/e2e_${name}.png`;

async function api(path, { method = "GET", body, token } = {}) {
  const res = await fetch(API + path, { method, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  if (!res.ok) throw new Error(`${method} ${path} -> ${res.status} ${text}`);
  return text ? JSON.parse(text) : null;
}

async function step(name, how, fn) {
  try {
    await fn();
    results.push({ name, how, status: "PASS" });
    console.log("PASS", name);
  } catch (error) {
    results.push({ name, how, status: "FAIL", note: String(error.message).split("\n")[0] });
    console.log("FAIL", name, "-", String(error.message).split("\n")[0]);
  }
}

async function login(page, email) {
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 240000 });
  await page.getByRole("textbox").filter({ visible: true }).first().fill(email);
  await page.locator("input[type=password]").filter({ visible: true }).first().fill(PASSWORD);
  await page.getByRole("button", { name: /^(sign in|sign in with email|continue with email)$/i }).filter({ visible: true }).first().click();
  await page.getByText("Meetings", { exact: true }).filter({ visible: true }).first().waitFor({ timeout: 120000 });
}

const owner = { email: `olive-${stamp}@example.com`, name: "Olive" };
const member = { email: `max-${stamp}@example.com`, name: "Max" };
let ownerToken, memberToken, workspace, meetingId;

const browser = await chromium.launch();
const ctx = (viewport = { width: 390, height: 844 }) => browser.newContext({ viewport });
const ownerPage = await (await ctx()).newPage();
const memberPage = await (await ctx()).newPage();
for (const p of [ownerPage, memberPage]) p.setDefaultTimeout(60000);

await step("Sign up two test accounts (owner and member)", "API", async () => {
  ownerToken = (await api("/auth/signup", { method: "POST", body: { email: owner.email, password: PASSWORD, display_name: owner.name } })).access_token;
  memberToken = (await api("/auth/signup", { method: "POST", body: { email: member.email, password: PASSWORD, display_name: member.name } })).access_token;
});

await step("Create a workspace and join it by code", "API", async () => {
  workspace = await api("/workspaces", { method: "POST", token: ownerToken, body: { name: `E2E ${stamp}` } });
  await api("/workspaces/join-by-code", { method: "POST", token: memberToken, body: { code: workspace.join_code } });
});

await step("Log in as the owner and see the empty Meetings list", "UI", async () => {
  await login(ownerPage, owner.email);
  await ownerPage.getByText("No meetings yet").filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("01_owner_empty") });
});

await step("Create a meeting with an attendee and a named guest", "UI", async () => {
  await ownerPage.getByRole("button", { name: "New meeting" }).filter({ visible: true }).first().click();
  await ownerPage.getByRole("textbox").filter({ visible: true }).first().fill("Weekly sync");
  await ownerPage.getByText("Max", { exact: true }).filter({ visible: true }).first().click();
  await ownerPage.getByRole("textbox").nth(1).fill("Imran");
  await ownerPage.getByRole("button", { name: "Add", exact: true }).click();
  await ownerPage.screenshot({ path: shot("02_new_meeting") });
  await ownerPage.getByRole("button", { name: "Create meeting" }).click();
  await ownerPage.getByText("Waiting for audio").filter({ visible: true }).first().waitFor();
  meetingId = ownerPage.url().split("/").pop();
  await ownerPage.screenshot({ path: shot("03_meeting_waiting") });
});

await step("Meeting warns that unenrolled people can't be named", "UI", async () => {
  await ownerPage.getByText(/hasn't enrolled, so their speech can't be named automatically/).filter({ visible: true }).first().waitFor();
});

await step("Consent screen: the owner agrees and confirms the guest", "UI", async () => {
  await ownerPage.getByRole("button", { name: "Review and agree" }).click();
  await ownerPage.getByText(/audio is sent to an outside speech-to-text service/i).filter({ visible: true }).first().waitFor();
  await ownerPage.getByRole("button", { name: "I agree to be recorded" }).click();
  await ownerPage.getByText("You agreed.").filter({ visible: true }).first().waitFor();
  await ownerPage.getByText("Imran agrees to be recorded").filter({ visible: true }).first().click();
  await ownerPage.screenshot({ path: shot("04_consent") });
  await ownerPage.getByRole("button", { name: "Done" }).filter({ visible: true }).first().click();
});

await step("Processing is blocked until the member also agrees", "API", async () => {
  const res = await fetch(`${API}/meetings/${meetingId}/audio/complete`, { method: "POST", headers: { Authorization: `Bearer ${ownerToken}` } });
  const body = await res.json();
  if (res.status !== 409 || !String(body.detail).includes("Max")) throw new Error(`expected 409 naming Max, got ${res.status} ${JSON.stringify(body)}`);
});

await step("The member logs in, sees the meeting and agrees", "UI", async () => {
  await login(memberPage, member.email);
  await memberPage.getByText("Weekly sync").filter({ visible: true }).first().click();
  await memberPage.getByText("Waiting for audio").filter({ visible: true }).first().waitFor();
  await memberPage.getByRole("button", { name: "Review and agree" }).click();
  await memberPage.getByRole("button", { name: "I agree to be recorded" }).click();
  await memberPage.getByText("You agreed.").filter({ visible: true }).first().waitFor();
  await memberPage.screenshot({ path: shot("05_member_consent") });
});

await step("Recorder screen is an honest placeholder (Vaniya's part)", "UI", async () => {
  await ownerPage.reload({ waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByRole("button", { name: "Record the meeting" }).filter({ visible: true }).first().click();
  await ownerPage.getByText("Recording is being built").filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("06_recorder_placeholder") });
  await ownerPage.getByRole("button", { name: "Back to the meeting" }).filter({ visible: true }).first().click();
});

await step("Record and upload from the app", "Vaniya's part", async () => {});
results.pop();
results.push({ name: "Record and upload from the app", how: "Vaniya's part", status: "NOT BUILT HERE" });

await step("Attach audio with the dev script (same endpoints Vaniya will call)", "script", async () => {
  const out = execFileSync("uv", ["run", "python", "../scripts/attach_audio_to_meeting.py", meetingId, CLIP], { cwd: "../backend", encoding: "utf8", timeout: 600000 });
  fs.writeFileSync(shot("07_script_output").replace(".png", ".txt"), out);
  if (!out.includes("Done.")) throw new Error(out.split("\n").slice(-3).join(" "));
});

await step("Meeting shows the transcript, summary, decisions and action items", "UI", async () => {
  await ownerPage.reload({ waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByRole("tab", { name: "Summary" }).filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("08_summary") });
  await ownerPage.getByRole("tab", { name: "Transcript" }).click();
  await ownerPage.getByText(/Unknown Speaker 1/).filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("09_transcript") });
  await ownerPage.getByRole("tab", { name: "Decisions" }).click();
  await ownerPage.screenshot({ path: shot("10_decisions") });
  await ownerPage.getByRole("tab", { name: "Action items" }).click();
  await ownerPage.screenshot({ path: shot("11_actions") });
});

await step("Rename Unknown Speaker 1 to Max, applied to the whole meeting", "UI", async () => {
  await ownerPage.getByRole("tab", { name: "Transcript" }).click();
  await ownerPage.getByText(/Unknown Speaker 1/).filter({ visible: true }).first().click();
  await ownerPage.getByText("Who is Unknown Speaker 1?").filter({ visible: true }).first().waitFor();
  await ownerPage.getByRole("button", { name: "Max", exact: true }).filter({ visible: true }).first().click();
  await ownerPage.getByText("Unknown Speaker 1").filter({ visible: true }).first().waitFor({ state: "detached", timeout: 15000 });
  await ownerPage.screenshot({ path: shot("12_renamed") });
});

await step("Tasks tab lists the action items; mark one done and undone", "UI", async () => {
  await ownerPage.goto(`${BASE}/tasks`, { waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByText(/Open · /).filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("13_tasks") });
  const box = ownerPage.getByRole("checkbox").filter({ visible: true }).first();
  await box.click();
  await ownerPage.getByText(/Done · 1/).filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("14_tasks_done") });
  await ownerPage.getByRole("checkbox").filter({ visible: true }).first().click();
  await ownerPage.getByText(/Open · /).filter({ visible: true }).first().waitFor();
});

await step("Meetings list shows the meeting with its status", "UI", async () => {
  await ownerPage.goto(`${BASE}/meetings`, { waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByText("Weekly sync").filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("15_list") });
});

await step("Members screen shows roles and the owner can make an admin", "UI", async () => {
  await ownerPage.goto(`${BASE}/workspaces/members`, { waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByText("Max").filter({ visible: true }).first().waitFor();
  await ownerPage.getByRole("button", { name: "Make admin" }).filter({ visible: true }).first().click();
  await ownerPage.getByText("Admin", { exact: true }).filter({ visible: true }).first().waitFor();
  await ownerPage.screenshot({ path: shot("16_members") });
});

await step("Assistant tab says coming soon", "UI", async () => {
  await ownerPage.goto(`${BASE}/assistant`, { waitUntil: "domcontentloaded", timeout: 240000 });
  await ownerPage.getByText("Coming soon").filter({ visible: true }).first().waitFor();
});

await step("Delete the member's account from Settings (password re-auth)", "UI", async () => {
  await memberPage.goto(`${BASE}/settings/delete-account`, { waitUntil: "domcontentloaded", timeout: 240000 });
  await memberPage.getByText("What gets deleted").filter({ visible: true }).first().waitFor();
  await memberPage.screenshot({ path: shot("17_delete_screen") });
  await memberPage.getByRole("button", { name: "Delete my account permanently" }).waitFor();
  await memberPage.locator("input[type=password]").filter({ visible: true }).first().fill("wrong password");
  await memberPage.getByRole("button", { name: "Delete my account permanently" }).click();
  await memberPage.getByText("That password is not right.").filter({ visible: true }).first().waitFor();
  await memberPage.locator("input[type=password]").filter({ visible: true }).first().fill(PASSWORD);
  await memberPage.getByRole("button", { name: "Delete my account permanently" }).click();
  await memberPage.getByRole("button", { name: /sign in/i }).filter({ visible: true }).first().waitFor();
  await memberPage.screenshot({ path: shot("18_after_delete") });
});

await step("After deletion the meeting shows Former member to the owner", "API", async () => {
  const detail = await api(`/meetings/${meetingId}`, { token: ownerToken });
  if (!detail.attendees.some((a) => a.kind === "former_member")) throw new Error("no former member attendee");
  const login2 = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: member.email, password: PASSWORD }) });
  if (login2.status !== 401) throw new Error("deleted account can still log in");
});

await browser.close();
fs.writeFileSync(`${SCRATCH}/e2e_results.json`, JSON.stringify({ owner: owner.email, member: member.email, meetingId, results }, null, 1));
console.log("\nSUMMARY");
for (const r of results) console.log(`${r.status.padEnd(15)} [${r.how}] ${r.name}${r.note ? " — " + r.note : ""}`);
