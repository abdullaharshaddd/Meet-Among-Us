// Design shell data – replace with API data

export const suggestions = [
  "What did we decide about voice enrollment?",
  "Which tasks are overdue for me?",
  "پچھلی میٹنگ میں کیا طے ہوا؟",
];

export const scopes = [
  { id: "all", label: "All meetings" },
  { id: "project-launch", label: "Spring launch" },
  { id: "meeting-sprint-sync", label: "Sprint sync" },
];

export interface MockCitation {
  label: string;
  meetingId: string;
  seconds: number;
}

export type MockReply =
  | { kind: "answer"; text: string; citations: MockCitation[] }
  | { kind: "action"; text: string; action: string; title: string; fields: { label: string; value: string }[] };

// Not a model. Picks a canned reply from a few words so every state of the screen can be seen.
export function mockReply(question: string): MockReply {
  const lower = question.toLowerCase();

  if (lower.includes("remind") || lower.includes("task") || lower.includes("create")) {
    return {
      kind: "action",
      text: "I can add that. Check the details first.",
      action: "Create task",
      title: "Send final artwork to the vendor",
      fields: [
        { label: "Owner", value: "Bilal Hussain" },
        { label: "Due", value: "Monday" },
        { label: "From", value: "Sprint sync · 02:44" },
      ],
    };
  }

  return {
    kind: "answer",
    text: "The team agreed to ship the three-passage enrollment and to review the gate threshold after two weeks of real data. Sara asked for the privacy message to appear before the first recording.",
    citations: [
      { label: "Sprint sync · 03:24", meetingId: "meeting-sprint-sync", seconds: 204 },
      { label: "Sprint sync · 01:14", meetingId: "meeting-sprint-sync", seconds: 74 },
    ],
  };
}
