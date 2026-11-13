import { useMutation, useQuery } from "@tanstack/react-query";
import { api, unwrap } from "./client";
import type { components } from "./types.gen";

export type DeletionPreview = components["schemas"]["DeletionPreviewResponse"];

export function useDeletionPreview() {
  return useQuery({
    queryKey: ["account", "deletion-preview"],
    queryFn: async () => unwrap(await api.GET("/account/deletion-preview")),
    // What would be deleted can change (someone leaves a workspace), so it is read fresh every time.
    gcTime: 0,
  });
}

// A password for a password account, or a fresh Google ID token for a Google one.
export function useDeleteAccount() {
  return useMutation({
    mutationFn: async (proof: { password?: string; google_id_token?: string }) =>
      unwrap(await api.POST("/account/delete", { body: proof })),
  });
}
