import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { orbitMembers, type MockMember } from "@/mocks/members";
import { api, unwrap } from "./client";
import type { components } from "./types.gen";

export type Workspace = components["schemas"]["WorkspaceResponse"];
export type WorkspaceRole = components["schemas"]["WorkspaceRole"];

export const workspacesKey = ["workspaces"] as const;

export function useWorkspaces() {
  return useQuery({
    queryKey: workspacesKey,
    queryFn: async () => unwrap(await api.GET("/workspaces")),
  });
}

// The workspace the person picked, or their first one until they pick.
export function useActiveWorkspace() {
  const { data: workspaces, isLoading } = useWorkspaces();
  const activeId = useWorkspaceStore((state) => state.activeWorkspaceId);

  const list = workspaces ?? [];
  const index = Math.max(0, list.findIndex((item) => item.id === activeId));

  return { workspace: list[index], workspaceIndex: index, workspaces: list, isLoading };
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  const setActiveWorkspaceId = useWorkspaceStore((state) => state.setActiveWorkspaceId);

  return useMutation({
    mutationFn: async (name: string) => unwrap(await api.POST("/workspaces", { body: { name } })),
    onSuccess: (workspace) => {
      setActiveWorkspaceId(workspace.id);
      return queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}

export function useJoinWorkspace() {
  const queryClient = useQueryClient();
  const setActiveWorkspaceId = useWorkspaceStore((state) => state.setActiveWorkspaceId);

  return useMutation({
    mutationFn: async (code: string) => unwrap(await api.POST("/workspaces/join-by-code", { body: { code } })),
    onSuccess: (workspace) => {
      setActiveWorkspaceId(workspace.id);
      return queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}

// Design shell data – replace with API data
// The two functions below have no backend route yet, so they answer from src/mocks.
// Screens only ever call these names, so swapping in real endpoints later touches this file alone.

export async function listMembers(workspaceId: string): Promise<MockMember[]> {
  void workspaceId;

  return orbitMembers;
}

export async function inviteMember(workspaceId: string, email: string): Promise<{ email: string }> {
  void workspaceId;

  return { email };
}

export function useMembers(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["workspaces", workspaceId, "members"],
    queryFn: () => listMembers(workspaceId ?? ""),
    enabled: Boolean(workspaceId),
  });
}

export function useInviteMember(workspaceId: string | undefined) {
  return useMutation({
    mutationFn: (email: string) => inviteMember(workspaceId ?? "", email),
  });
}
