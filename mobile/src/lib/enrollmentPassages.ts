import type { EnrollmentLanguage } from "@/api/enrollment";
import { generatedPassages, minSpeechSeconds } from "./enrollmentPassages.gen";

export type Passage = {
  language: EnrollmentLanguage;
  title: string;
  text: string;
  isUrdu: boolean;
};

// The text and the speech minimum are generated from the backend's one copy
// (backend/app/content/enrollment_passages.json). Run `npm run generate:passages`
// after it changes. The order is the order the user records them in.
export const passages: Passage[] = generatedPassages;

export { minSpeechSeconds };

export function findPassage(language: string | undefined): Passage | undefined {
  return passages.find((passage) => passage.language === language);
}

export function passageNumber(language: EnrollmentLanguage): number {
  return passages.findIndex((passage) => passage.language === language) + 1;
}
