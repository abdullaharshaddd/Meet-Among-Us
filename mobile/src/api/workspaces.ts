import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useWorkspaceStore } from "@/store/workspaceStore";
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

export type WorkspaceMember = components["schemas"]["WorkspaceMemberResponse"];
export type Invite = components["schemas"]["InviteResponse"];

const membersKey = (workspaceId: string | undefined) => ["workspaces", workspaceId, "members"] as const;
const invitesKey = (workspaceId: string | undefined) => ["workspaces", workspaceId, "invites"] as const;

export function useMembers(workspaceId: string | undefined) {
  return useQuery({
    queryKey: membersKey(workspaceId),
    enabled: Boolean(workspaceId),
    queryFn: async () =>
      unwrap(await api.GET("/workspaces/{workspace_id}/members", { params: { path: { workspace_id: workspaceId ?? "" } } })),
  });
}

export function useInvites(workspaceId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: invitesKey(workspaceId),
    enabled: Boolean(workspaceId) && enabled,
    queryFn: async () =>
      unwrap(await api.GET("/workspaces/{workspace_id}/invites", { params: { path: { workspace_id: workspaceId ?? "" } } })),
    // The email is sent in the background, so its status changes a moment after the invite is made.
    refetchInterval: 5_000,
  });
}

export function useInviteMember(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (email: string) =>
      unwrap(await api.POST("/workspaces/{workspace_id}/invites", { params: { path: { workspace_id: workspaceId ?? "" } }, body: { email } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invitesKey(workspaceId) }),
  });
}

export function useRevokeInvite(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (inviteId: string) =>
      unwrap(
        await api.POST("/workspaces/{workspace_id}/invites/{invite_id}/revoke", {
          params: { path: { workspace_id: workspaceId ?? "", invite_id: inviteId } },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invitesKey(workspaceId) }),
  });
}

export function useResendInvite(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (inviteId: string) =>
      unwrap(
        await api.POST("/workspaces/{workspace_id}/invites/{invite_id}/resend", {
          params: { path: { workspace_id: workspaceId ?? "", invite_id: inviteId } },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invitesKey(workspaceId) }),
  });
}

export function useChangeRole(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { userId: string; role: "admin" | "member" }) =>
      unwrap(
        await api.PATCH("/workspaces/{workspace_id}/members/{user_id}/role", {
          params: { path: { workspace_id: workspaceId ?? "", user_id: input.userId } },
          body: { role: input.role },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKey(workspaceId) }),
  });
}

// Also how a person leaves: removing yourself.
export function useRemoveMember(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) =>
      unwrap(
        await api.DELETE("/workspaces/{workspace_id}/members/{user_id}", {
          params: { path: { workspace_id: workspaceId ?? "", user_id: userId } },
        }),
      ),
    onSuccess: () => Promise.all([queryClient.invalidateQueries({ queryKey: membersKey(workspaceId) }), queryClient.invalidateQueries({ queryKey: workspacesKey })]),
  });
}

export function useTransferOwnership(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) =>
      unwrap(
        await api.POST("/workspaces/{workspace_id}/transfer-ownership", {
          params: { path: { workspace_id: workspaceId ?? "" } },
          body: { user_id: userId },
        }),
      ),
    onSuccess: () => Promise.all([queryClient.invalidateQueries({ queryKey: membersKey(workspaceId) }), queryClient.invalidateQueries({ queryKey: workspacesKey })]),
  });
}

// The long personal invite code from an invite email. It joins the workspace the same way a join code does.
export function useAcceptInvite() {
  const queryClient = useQueryClient();
  const setActiveWorkspaceId = useWorkspaceStore((state) => state.setActiveWorkspaceId);

  return useMutation({
    mutationFn: async (token: string) => unwrap(await api.POST("/invites/accept", { body: { token: token.trim() } })),
    onSuccess: (workspace) => {
      setActiveWorkspaceId(workspace.id);

      return queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}
