// Design shell data – replace with API data
import { projectName } from "./projects";

export type MockMeetingStatus = "upcoming" | "live" | "processing" | "ready" | "failed";

export interface MockMeeting {
  id: string;
  workspaceId: string;
  projectId: string;
  title: string;
  startsAt: Date;
  durationMinutes?: number;
  status: MockMeetingStatus;
  participantIds: string[];
}

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

// Offsets from now, so "upcoming" is always in the future whenever the app opens.
function at(offsetMilliseconds: number): Date {
  return new Date(Date.now() + offsetMilliseconds);
}

const orbitMeetings: MockMeeting[] = [
  {
    id: "meeting-design-review",
    workspaceId: "ws-orbit",
    projectId: "project-launch",
    title: "Design review — onboarding flow",
    startsAt: at(-0.4 * HOUR),
    status: "live",
    participantIds: ["user-ayesha", "user-bilal", "user-sara", "guest-omar"],
  },
  {
    id: "meeting-planning",
    workspaceId: "ws-orbit",
    projectId: "project-launch",
    title: "Quarterly planning",
    startsAt: at(0.3 * DAY),
    status: "upcoming",
    participantIds: ["user-ayesha", "user-hamza", "user-noor"],
  },
  {
    id: "meeting-vendor",
    workspaceId: "ws-orbit",
    projectId: "project-ops",
    title: "Vendor call — پرنٹنگ کا بجٹ",
    startsAt: at(1.6 * DAY),
    status: "upcoming",
    participantIds: ["user-ayesha", "user-sara", "guest-omar"],
  },
  {
    id: "meeting-sprint-sync",
    workspaceId: "ws-orbit",
    projectId: "project-launch",
    title: "Sprint sync",
    startsAt: at(-1 * DAY),
    durationMinutes: 48,
    status: "ready",
    participantIds: ["user-ayesha", "user-bilal", "user-sara", "guest-omar", "user-hamza"],
  },
  {
    id: "meeting-hiring",
    workspaceId: "ws-orbit",
    projectId: "project-hiring",
    title: "Hiring panel debrief",
    startsAt: at(-2 * DAY),
    durationMinutes: 31,
    status: "processing",
    participantIds: ["user-ayesha", "user-noor", "user-hamza"],
  },
  {
    id: "meeting-retro",
    workspaceId: "ws-orbit",
    projectId: "project-ops",
    title: "Ops retro — اگلے ہفتے کی ترجیحات",
    startsAt: at(-6 * DAY),
    durationMinutes: 62,
    status: "ready",
    participantIds: ["user-ayesha", "user-bilal", "user-noor"],
  },
  {
    id: "meeting-failed",
    workspaceId: "ws-orbit",
    projectId: "project-ops",
    title: "Supplier check-in",
    startsAt: at(-9 * DAY),
    durationMinutes: 12,
    status: "failed",
    participantIds: ["user-ayesha", "user-sara"],
  },
];

// Only the first mock workspace has meetings, which is how the empty state gets exercised.
export function listMeetings(workspaceIndex: number): MockMeeting[] {
  return workspaceIndex === 0 ? orbitMeetings : [];
}

export function findMeeting(id: string): MockMeeting | undefined {
  return orbitMeetings.find((meeting) => meeting.id === id);
}

export function meetingProjectName(meeting: MockMeeting): string {
  return projectName(meeting.projectId);
}
