// Design shell data – replace with API data

export interface MockTask {
  id: string;
  title: string;
  source: string;
  // Days from today. Negative is overdue.
  dueInDays: number;
  assigneeId: string;
  assigneeName: string;
  isDone: boolean;
}

export const initialTasks: MockTask[] = [
  { id: "t1", title: "Send final artwork to the vendor", source: "Sprint sync", dueInDays: -2, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: false },
  { id: "t2", title: "Confirm printing quote — پرنٹنگ کا بجٹ", source: "Vendor call", dueInDays: -1, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: false },
  { id: "t3", title: "Draft the Urdu welcome copy", source: "Sprint sync", dueInDays: 0, assigneeId: "user-sara", assigneeName: "Sara Khan", isDone: false },
  { id: "t4", title: "Book the consent-form review", source: "Design review", dueInDays: 0, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: false },
  { id: "t5", title: "Share enrollment drop-off numbers", source: "Quarterly planning", dueInDays: 3, assigneeId: "user-bilal", assigneeName: "Bilal Hussain", isDone: false },
  { id: "t6", title: "Interview scorecards to the panel", source: "Hiring panel debrief", dueInDays: 4, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: false },
  { id: "t7", title: "Review gate threshold with real data", source: "Sprint sync", dueInDays: 14, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: false },
  { id: "t8", title: "Archive the old onboarding deck", source: "Ops retro", dueInDays: -5, assigneeId: "user-ayesha", assigneeName: "Ayesha Siddiqui", isDone: true },
];
