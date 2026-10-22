import type { EnrollmentLanguage } from "@/api/enrollment";

export type Passage = {
  language: EnrollmentLanguage;
  title: string;
  text: string;
  isUrdu: boolean;
};

// Same text as docs/ENROLLMENT_PASSAGES.md. The order here is the order the
// user records them in.
export const passages: Passage[] = [
  {
    language: "en",
    title: "English",
    text: "Most mornings I like to take a slow walk before the city gets loud, just to clear my head and notice how the light changes along the way.",
    isUrdu: false,
  },
  {
    language: "ur",
    title: "Urdu",
    text: "مجھے صبح کی چائے کے بغیر دن شروع ہی نہیں لگتا، چاہے کام کتنا بھی زیادہ ہو، تھوڑی دیر سکون سے بیٹھ کر چائے ضرور پیتا ہوں۔",
    isUrdu: true,
  },
  {
    language: "mixed",
    title: "Code-switched",
    text: "یار، deadline زیادہ دور نہیں، لیکن client سے requirements ابھی تک clear نہیں ہوئی، اس لیے میں پہلے ایک quick call schedule کرنا چاہتا ہوں تاکہ confusion نہ رہے۔",
    isUrdu: true,
  },
];

export function findPassage(language: string | undefined): Passage | undefined {
  return passages.find((passage) => passage.language === language);
}

export function passageNumber(language: EnrollmentLanguage): number {
  return passages.findIndex((passage) => passage.language === language) + 1;
}
