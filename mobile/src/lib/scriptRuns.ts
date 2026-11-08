export interface Run {
  text: string;
  isUrdu: boolean;
}

// The Arabic block already holds the Urdu comma, question mark and full stop,
// so punctuation at the end of a sentence stays with the Urdu run.
const ARABIC_SCRIPT = "\\u0600-\\u06FF\\u0750-\\u077F\\uFB50-\\uFDFF\\uFE70-\\uFEFF";
const URDU_RUN = new RegExp(`([${ARABIC_SCRIPT}]+(?:\\s+[${ARABIC_SCRIPT}]+)*)`);

// Splits a string into alternating Urdu and non-Urdu runs. Spaces between two
// Urdu words stay inside the Urdu run, so a run never starts or ends mid-phrase.
export function splitRuns(text: string): Run[] {
  // Splitting on a capture group puts every Urdu run at an odd index.
  return text
    .split(URDU_RUN)
    .map((piece, index) => ({ text: piece, isUrdu: index % 2 === 1 }))
    .filter((run) => run.text !== "");
}

export type TextDirection = "rtl" | "ltr";

const LATIN_LETTER = /[A-Za-z]/;

// For text with no known language (chat, free text): the script with more words wins,
// and a tie goes to right-to-left, since code-switched Urdu often opens with an English name.
// Digits and punctuation don't vote.
export function guessDirection(text: string): TextDirection {
  const runs = splitRuns(text);
  let urduWords = 0;
  let latinWords = 0;

  for (const run of runs) {
    const words = run.text.split(/\s+/).filter((word) => (run.isUrdu ? word !== "" : LATIN_LETTER.test(word)));

    if (words.length === 0) continue;

    if (run.isUrdu) urduWords += words.length;
    else latinWords += words.length;
  }

  if (urduWords === 0 && latinWords === 0) return "ltr";

  return urduWords >= latinWords ? "rtl" : "ltr";
}
