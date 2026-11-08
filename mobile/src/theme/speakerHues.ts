// For dots, thin bars and avatar rings only. Never for text: some of these
// are under 3:1 on the Paper canvas, so a name always sits beside the hue.
export const speakerHues = ["#2F6FED", "#0F9D8A", "#B4499C", "#C98A00", "#6A5ACD", "#3E8E2F"] as const;

// The same id always lands on the same hue, in every meeting and every theme.
export function speakerHue(speakerId: string): string {
  let hash = 0;

  for (const character of speakerId) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  }

  return speakerHues[hash % speakerHues.length];
}
