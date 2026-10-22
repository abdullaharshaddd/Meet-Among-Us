import { Platform } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, unwrap } from "./client";
import type { components } from "./types.gen";

export type EnrollmentLanguage = components["schemas"]["EnrollmentLanguage"];
export type EnrollmentStatus = components["schemas"]["EnrollmentStatus"];
export type EnrollmentStatusResponse = components["schemas"]["EnrollmentStatusResponse"];
export type PassageStatus = components["schemas"]["PassageStatus"];
export type UploadUrlResponse = components["schemas"]["UploadUrlResponse"];
export type SubmitSampleResponse = components["schemas"]["SubmitSampleResponse"];

// Phones record AAC in m4a; a browser records webm. Both are accepted by the
// backend, see ADR-0019.
const isWeb = Platform.OS === "web";
const uploadFormat = isWeb ? "webm" : "m4a";
const uploadContentType = isWeb ? "audio/webm" : "audio/mp4";

export const enrollmentStatusKey = ["enrollment", "status"] as const;

export function useEnrollmentStatus() {
  return useQuery({
    queryKey: enrollmentStatusKey,
    queryFn: async () => unwrap(await api.GET("/enrollment/status")),
  });
}

export function useRequestUploadUrl() {
  return useMutation({
    mutationFn: async (language: EnrollmentLanguage) =>
      unwrap(await api.POST("/enrollment/uploads", { body: { language, audio_format: uploadFormat } })),
  });
}

type UploadRecordingInput = {
  uploadUrl: string;
  fileUri: string;
};

// A plain fetch, not the `api` client: the presigned URL points at R2, not our
// backend, and R2 rejects requests that carry our Authorization header.
export function useUploadRecording() {
  return useMutation({
    mutationFn: async ({ uploadUrl, fileUri }: UploadRecordingInput) => {
      const fileResponse = await fetch(fileUri);
      const fileBlob = await fileResponse.blob();

      // Must match the Content-Type the backend signed for this format.
      const uploadResponse = await fetch(uploadUrl, {
        method: "PUT",
        headers: { "Content-Type": uploadContentType },
        body: fileBlob,
      });

      if (!uploadResponse.ok) {
        throw new ApiError(uploadResponse.status, { detail: "Upload to storage failed" });
      }
    },
  });
}

type SubmitSampleInput = {
  language: EnrollmentLanguage;
  audioKey: string;
};

export function useSubmitSample() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ language, audioKey }: SubmitSampleInput) =>
      unwrap(await api.POST("/enrollment/samples", { body: { language, audio_key: audioKey } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: enrollmentStatusKey }),
  });
}

export function useResetEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => unwrap(await api.DELETE("/enrollment")),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: enrollmentStatusKey }),
  });
}
