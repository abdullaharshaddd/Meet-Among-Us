import { create } from "zustand";
import type { EnrollmentLanguage } from "@/api/enrollment";

// Holds only the recording the user is working on right now. Everything the
// server knows about enrollment lives in TanStack Query, not here.
type EnrollmentDraftState = {
  language: EnrollmentLanguage | null;
  fileUri: string | null;
  setRecording: (language: EnrollmentLanguage, fileUri: string) => void;
  clearRecording: () => void;
};

export const useEnrollmentDraftStore = create<EnrollmentDraftState>((set) => ({
  language: null,
  fileUri: null,
  setRecording: (language, fileUri) => set({ language, fileUri }),
  clearRecording: () => set({ language: null, fileUri: null }),
}));
