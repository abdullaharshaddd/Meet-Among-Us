// Screenshots of every screen in Paper and Studio, at phone size, with the API faked.
// Run Expo web first (npx expo start --web --port 8081), then: npm run shots
// Optional: npm run shots -- meetings   (only routes whose name contains "meetings")
import { mkdirSync } from "node:fs";
import { chromium } from "playwright";

const BASE = process.env.SHOTS_URL ?? "http://localhost:8081";
const OUT = new URL("../.shots/", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const FILTER = process.argv[2];

const USER = {
  id: "00000000-0000-7000-8000-000000000001",
  email: "ayesha@orbitlabs.example",
  display_name: "Ayesha Siddiqui",
  avatar_url: null,
  enrollment_status: "complete",
  created_at: "2026-01-01T00:00:00Z",
};

const WORKSPACES = [
  {
    id: "00000000-0000-7000-8000-0000000000a1",
    name: "Orbit Labs",
    owner_user_id: USER.id,
    created_at: "2026-01-01T00:00:00Z",
    my_role: "owner",
    can_create_projects: true,
    join_code: "K7QM2XPD",
    code_joining_enabled: true,
  },
  {
    id: "00000000-0000-7000-8000-0000000000a2",
    name: "Thesis group",
    owner_user_id: "00000000-0000-7000-8000-000000000009",
    created_at: "2026-02-01T00:00:00Z",
    my_role: "member",
    can_create_projects: false,
    join_code: null,
    code_joining_enabled: true,
  },
];

const passage = (language, state) => ({ language, state, reason_code: null, reason_message: null });

const ENROLLMENT = {
  enrolled: {
    enrollment_status: "complete",
    passages: [passage("en", "accepted"), passage("ur", "accepted"), passage("mixed", "accepted")],
  },
  notEnrolled: {
    enrollment_status: "in_progress",
    passages: [passage("en", "accepted"), passage("ur", "pending"), passage("mixed", "pending")],
  },
};

// Each entry: where to go once signed in, and what to do before the picture.
const ROUTES = [
  { name: "login", auth: false, path: "/" },
  { name: "signup", auth: false, path: "/", then: { text: "Create one" } },
  { name: "design-system", auth: false, path: "/design-system", scrolls: 14 },
  { name: "meetings", path: "/meetings" },
  { name: "meetings-not-enrolled", path: "/meetings", enrolled: false },
  { name: "meetings-scrolled", path: "/meetings", scrollBy: 500 },
  { name: "meetings-switcher", path: "/meetings", click: { label: /Workspace Orbit Labs/ } },
  { name: "meetings-project-sheet", path: "/meetings", click: { label: "Start meeting" } },
  { name: "meetings-consent-sheet", path: "/meetings", click: { label: "Start meeting" }, then: { text: "Continue" } },
  { name: "meetings-empty", path: "/meetings", click: { label: /Workspace Orbit Labs/ }, then: { text: "Thesis group" } },
  { name: "live", path: "/meetings", open: /Design review/, wait: 2500 },
  { name: "meeting-detail-summary", path: "/meetings", open: /Sprint sync/ },
  { name: "meeting-detail-transcript", path: "/meetings", open: /Sprint sync/, then: { tab: "Transcript" }, wait: 400 },
  { name: "meeting-citation-jump", path: "/meetings", open: /Sprint sync/, then: { text: "Sprint sync · 03:24" }, wait: 900 },
  { name: "meeting-rename-sheet", path: "/meetings", open: /Sprint sync/, then: { tab: "Transcript" }, click: { label: /Unknown Speaker 1/ } },
  { name: "assistant", nav: [{ tab: "Assistant" }] },
  { name: "assistant-chat", nav: [{ tab: "Assistant" }], type: "Create a task from the vendor call", wait: 2200 },
  { name: "tasks", nav: [{ tab: "Tasks" }] },
  { name: "tasks-all", nav: [{ tab: "Tasks" }, { button: "All" }] },
  { name: "tasks-done", nav: [{ tab: "Tasks" }, { button: "Done" }] },
  { name: "tasks-new", nav: [{ tab: "Tasks" }, { button: "New task" }] },
  { name: "settings", nav: [{ tab: "Settings" }] },
  { name: "settings-signout", nav: [{ tab: "Settings" }, { button: "Sign out" }] },
  { name: "settings-scrolled", nav: [{ tab: "Settings" }], scrollBy: 1200 },
  { name: "enroll-intro", enrolled: false, nav: [{ button: /Continue enrollment/ }] },
  { name: "enroll-permission", enrolled: false, nav: [{ button: /Continue enrollment/ }, { button: "Continue" }] },
  { name: "enroll-record", enrolled: false, mic: true, nav: [{ button: /Continue enrollment/ }, { button: "Continue" }], wait: 1200 },
  { name: "enroll-recording", enrolled: false, mic: true, nav: [{ button: /Continue enrollment/ }, { button: "Continue" }, { button: "Start recording" }], wait: 2500 },
  { name: "workspaces-create", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Create a workspace" }] },
  { name: "workspaces-join", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Join with a code" }] },
  { name: "workspaces-created", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Create a workspace" }], type: "Orbit Labs", submit: "Create workspace", wait: 1500 },
  { name: "workspaces-join-typed", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Join with a code" }], type: "k7qm2xp", submit: false, wait: 500 },
  { name: "workspaces-invite", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Members" }, { button: "Invite by email" }] },
  { name: "workspaces-members", nav: [{ button: /Workspace Orbit Labs/ }, { button: "Members" }] },
];

function mockApi(context, enrollment) {
  return context.route(
    (url) => /\/(auth|enrollment|workspaces)(\/|$)/.test(url.pathname) && url.port !== new URL(BASE).port,
    (route) => {
      const { pathname } = new URL(route.request().url());
      const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

      if (pathname.endsWith("/auth/login") || pathname.endsWith("/auth/signup")) {
        return json({ access_token: "shot-access", refresh_token: "shot-refresh", token_type: "bearer", user: USER });
      }
      if (pathname.endsWith("/enrollment/status")) return json(enrollment);
      if (pathname.endsWith("/workspaces")) return json(route.request().method() === "POST" ? WORKSPACES[0] : WORKSPACES);
      if (pathname.endsWith("/workspaces/join-by-code")) return json(WORKSPACES[1]);

      return json({ detail: "not mocked" }, 404);
    },
  );
}

async function signIn(page) {
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.getByRole("textbox").first().fill(USER.email);
  await page.locator("input[type=password]").first().fill("password123");
  await page.getByRole("button", { name: /^(sign in|sign in with email|continue with email)$/i }).first().click();
  await page.waitForTimeout(1500);
}

// Moves inside the running app without a reload, so the fake session survives.
async function goTo(page, path) {
  await page.evaluate((target) => {
    window.history.pushState({}, "", target);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, path);
  await page.waitForTimeout(1200);
}

async function scrollMain(page, by) {
  await page.evaluate((distance) => {
    const scrollers = [...document.querySelectorAll("*")].filter((el) => el.scrollHeight > el.clientHeight + 20 && getComputedStyle(el).overflowY !== "visible");
    scrollers.sort((a, b) => b.scrollHeight - a.scrollHeight);
    for (const scroller of scrollers) scroller.scrollBy(0, distance);
  }, by);
  await page.waitForTimeout(500);
}

async function run() {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"] });

  for (const scheme of ["light", "dark"]) {
    const label = scheme === "light" ? "paper" : "studio";

    for (const route of ROUTES.filter((item) => !FILTER || item.name.includes(FILTER))) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: scheme, deviceScaleFactor: 1, permissions: route.mic ? ["microphone"] : [] });
      const page = await context.newPage();
      page.on("pageerror", (error) => console.log(`  [${label}/${route.name}] page error: ${error.message}`));
      page.on("console", (message) => {
        if (message.type() === "error" && !/Failed to load resource|favicon/.test(message.text())) {
          console.log(`  [${label}/${route.name}] console: ${message.text().slice(0, 200)}`);
        }
      });

      await mockApi(context, route.enrolled === false ? ENROLLMENT.notEnrolled : ENROLLMENT.enrolled);

      try {
        if (route.auth === false) {
          await page.goto(BASE + (route.path === "/" ? "" : route.path), { waitUntil: "networkidle" });
          await page.waitForTimeout(1500);
        } else {
          await signIn(page);
          if (route.path) await goTo(page, route.path);

          for (const step of route.nav ?? []) {
            const target = step.tab ? page.getByRole("tab", { name: step.tab }) : page.getByRole("button", { name: step.button });
            await target.first().click();
            await page.waitForTimeout(1300);
          }
        }

        // Pages with a dynamic id are reached by tapping, the way a person would.
        if (route.open) {
          await page.getByRole("button", { name: route.open }).first().click();
          await page.waitForTimeout(1500);
        }

        if (route.then?.tab) {
          await page.getByRole("tab", { name: route.then.tab }).first().click();
          await page.waitForTimeout(700);
        }
        if (route.click) {
          await page.getByRole("button", { name: route.click.label }).first().click();
          await page.waitForTimeout(1300);
        }
        if (route.then?.text) {
          await page.getByText(route.then.text, { exact: true }).first().click();
          await page.waitForTimeout(1300);
        }
        if (route.type) {
          await page.getByRole("textbox").last().fill(route.type);
          if (route.submit !== false) await page.getByRole("button", { name: route.submit ?? "Send" }).click();
        }
        if (route.wait) await page.waitForTimeout(route.wait);
        if (route.scrollBy) await scrollMain(page, route.scrollBy);

        const steps = route.scrolls ?? 1;
        for (let step = 0; step < steps; step += 1) {
          const suffix = steps > 1 ? `-${step + 1}` : "";
          await page.screenshot({ path: `${OUT}${route.name}${suffix}.${label}.png` });
          if (steps > 1) await scrollMain(page, 700);
        }

        console.log(`ok   ${label}/${route.name}`);
      } catch (error) {
        console.log(`FAIL ${label}/${route.name}: ${String(error.message).split("\n")[0]}`);
        await page.screenshot({ path: `${OUT}${route.name}.${label}.FAILED.png` }).catch(() => {});
      }

      await context.close();
    }
  }

  await browser.close();
}

run();
