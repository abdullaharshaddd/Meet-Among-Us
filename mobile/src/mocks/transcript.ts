// Design shell data – replace with API data
import type { SegmentLanguage, TranscriptSpeaker } from "@/components/ui";

export interface MockSegment {
  id: string;
  startSeconds: number;
  speaker: TranscriptSpeaker;
  language: SegmentLanguage;
  text: string;
}

const ayesha: TranscriptSpeaker = { kind: "member", id: "user-ayesha", name: "Ayesha Siddiqui" };
const bilal: TranscriptSpeaker = { kind: "member", id: "user-bilal", name: "Bilal Hussain" };
const sara: TranscriptSpeaker = { kind: "member", id: "user-sara", name: "Sara Khan" };
const omar: TranscriptSpeaker = { kind: "guest", id: "guest-omar", name: "Omar Farooq" };

export const unknownOne: TranscriptSpeaker = { kind: "unknown", id: "unknown-1", number: 1 };
export const unknownTwo: TranscriptSpeaker = { kind: "unknown", id: "unknown-2", number: 2 };

export const segments: MockSegment[] = [
  { id: "s1", startSeconds: 12, speaker: ayesha, language: "en", text: "Let's start with the onboarding flow. Bilal, where did we land on the voice step?" },
  { id: "s2", startSeconds: 31, speaker: bilal, language: "mixed", text: "Voice step ab teen passages ka hai — انگریزی، اردو، اور mixed۔ Two minutes in total." },
  { id: "s3", startSeconds: 74, speaker: sara, language: "ur", text: "میرے خیال میں ہمیں پہلے رازداری کا پیغام دکھانا چاہیے۔" },
  { id: "s4", startSeconds: 118, speaker: omar, language: "en", text: "From the vendor side, we can print the welcome cards by the fifteenth if the artwork arrives on Monday." },
  { id: "s5", startSeconds: 163, speaker: unknownOne, language: "mixed", text: "Ali نے 3 tasks لیے ہیں، باقی کل تک ہو جائیں گے۔" },
  { id: "s6", startSeconds: 204, speaker: ayesha, language: "en", text: "Good. So the decision is: ship the three-passage enrollment, and review the gate threshold after two weeks of real data." },
  { id: "s7", startSeconds: 246, speaker: unknownOne, language: "ur", text: "ٹھیک ہے، میں آج شام تک ڈیزائن فائلیں بھیج دوں گا۔" },
  { id: "s8", startSeconds: 289, speaker: unknownTwo, language: "en", text: "Can we also add the Urdu welcome copy to the same print run?" },
  { id: "s9", startSeconds: 332, speaker: bilal, language: "mixed", text: "Haan, Sara ko copy bhejni hogi — ہم جمعرات 15:00 تک فائنل کر لیں گے۔" },
  { id: "s10", startSeconds: 371, speaker: sara, language: "en", text: "I'll draft it tonight and share it in the project channel." },
];

export const summary = {
  overview:
    "The team reviewed the onboarding flow and agreed to ship three-passage voice enrollment. The vendor can print welcome cards by the fifteenth if artwork arrives on Monday.",
  points: [
    "Voice enrollment stays at three passages: English, Urdu and mixed.",
    "The privacy message is shown before the first recording.",
    "Welcome cards go to print in one run, English and Urdu together.",
  ],
};

export interface MockDecision {
  id: string;
  text: string;
  atSeconds: number;
}

export const decisions: MockDecision[] = [
  { id: "d1", text: "Ship the three-passage enrollment and review the gate threshold after two weeks.", atSeconds: 204 },
  { id: "d2", text: "Show the privacy message before the first recording.", atSeconds: 74 },
  { id: "d3", text: "Print English and Urdu welcome cards in a single run.", atSeconds: 289 },
];

export interface MockActionItem {
  id: string;
  title: string;
  ownerId: string;
  ownerName: string;
  dueLabel: string;
}

export const actionItems: MockActionItem[] = [
  { id: "a1", title: "Send final artwork to the vendor", ownerId: "user-bilal", ownerName: "Bilal Hussain", dueLabel: "Mon" },
  { id: "a2", title: "Draft the Urdu welcome copy", ownerId: "user-sara", ownerName: "Sara Khan", dueLabel: "Tonight" },
  { id: "a3", title: "Review gate threshold with real data", ownerId: "user-ayesha", ownerName: "Ayesha Siddiqui", dueLabel: "In 2 weeks" },
];

export function formatClock(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
