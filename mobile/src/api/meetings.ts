import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, unwrap } from "./client";
import type { components } from "./types.gen";

export type MeetingDetail = components["schemas"]["MeetingDetailResponse"];
export type MeetingListItem = components["schemas"]["MeetingListItem"];
export type MeetingStatus = components["schemas"]["MeetingStatus"];
export type Attendee = components["schemas"]["AttendeeResponse"];
export type Segment = components["schemas"]["SegmentResponse"];
export type Citation = components["schemas"]["CitationResponse"];
export type Task = components["schemas"]["TaskResponse"];

export const meetingsKey = (workspaceId: string | undefined) => ["meetings", "list", workspaceId] as const;
export const meetingKey = (meetingId: string) => ["meetings", "detail", meetingId] as const;
export const tasksKey = ["tasks"] as const;

export function useMeetings(workspaceId: string | undefined) {
  return useQuery({
    queryKey: meetingsKey(workspaceId),
    enabled: Boolean(workspaceId),
    queryFn: async () =>
      unwrap(await api.GET("/workspaces/{workspace_id}/meetings", { params: { path: { workspace_id: workspaceId ?? "" } } })),
    // Statuses change on their own (processing finishes), so the list refreshes while it is open.
    refetchInterval: 10_000,
  });
}

// Polls while the meeting is waiting or processing, so consent and progress appear without a refresh.
export function useMeeting(meetingId: string | undefined) {
  return useQuery({
    queryKey: meetingKey(meetingId ?? ""),
    enabled: Boolean(meetingId),
    queryFn: async () => unwrap(await api.GET("/meetings/{meeting_id}", { params: { path: { meeting_id: meetingId ?? "" } } })),
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status === "processing") return 3_000;
      if (status === "waiting_for_audio") return 6_000;

      return false;
    },
  });
}

// Mutations that answer with the whole meeting put it straight into the cache.
function useMeetingUpdater(meetingId: string) {
  const queryClient = useQueryClient();

  return (detail: MeetingDetail) => {
    queryClient.setQueryData(meetingKey(meetingId), detail);
    void queryClient.invalidateQueries({ queryKey: ["meetings", "list"] });
    void queryClient.invalidateQueries({ queryKey: tasksKey });
  };
}

export function useCreateMeeting(workspaceId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: { title: string; attendee_user_ids: string[]; guest_names: string[] }) =>
      unwrap(await api.POST("/workspaces/{workspace_id}/meetings", { params: { path: { workspace_id: workspaceId ?? "" } }, body })),
    onSuccess: (detail) => {
      queryClient.setQueryData(meetingKey(detail.id), detail);

      return queryClient.invalidateQueries({ queryKey: ["meetings", "list"] });
    },
  });
}

export function useConsentNotice() {
  return useQuery({
    queryKey: ["meetings", "consent-notice"],
    queryFn: async () => unwrap(await api.GET("/meetings/consent-notice")),
    staleTime: Infinity,
  });
}

export function useSetConsent(meetingId: string) {
  const update = useMeetingUpdater(meetingId);

  return useMutation({
    mutationFn: async (input: { attendeeId: string; granted: boolean }) =>
      unwrap(
        await api.PUT("/meetings/{meeting_id}/attendees/{attendee_id}/consent", {
          params: { path: { meeting_id: meetingId, attendee_id: input.attendeeId } },
          body: { granted: input.granted },
        }),
      ),
    onSuccess: update,
  });
}

export function useAddAttendee(meetingId: string) {
  const update = useMeetingUpdater(meetingId);

  return useMutation({
    mutationFn: async (body: { user_id?: string; guest_name?: string }) =>
      unwrap(await api.POST("/meetings/{meeting_id}/attendees", { params: { path: { meeting_id: meetingId } }, body })),
    onSuccess: update,
  });
}

export function useRemoveAttendee(meetingId: string) {
  const update = useMeetingUpdater(meetingId);

  return useMutation({
    mutationFn: async (attendeeId: string) =>
      unwrap(
        await api.DELETE("/meetings/{meeting_id}/attendees/{attendee_id}", {
          params: { path: { meeting_id: meetingId, attendee_id: attendeeId } },
        }),
      ),
    onSuccess: update,
  });
}

export function useRetryMeeting(meetingId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => unwrap(await api.POST("/meetings/{meeting_id}/retry", { params: { path: { meeting_id: meetingId } } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: meetingKey(meetingId) }),
  });
}

export function useRenameSpeaker(meetingId: string) {
  const update = useMeetingUpdater(meetingId);

  return useMutation({
    mutationFn: async (input: { unknownNumber: number; attendeeId?: string; guestName?: string }) =>
      unwrap(
        await api.PUT("/meetings/{meeting_id}/speaker-renames/{unknown_number}", {
          params: { path: { meeting_id: meetingId, unknown_number: input.unknownNumber } },
          body: { attendee_id: input.attendeeId ?? null, guest_name: input.guestName ?? null },
        }),
      ),
    onSuccess: update,
  });
}

export function useTasks() {
  return useQuery({
    queryKey: tasksKey,
    queryFn: async () => unwrap(await api.GET("/me/action-items")),
  });
}

export function useSetTaskDone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { id: string; done: boolean }) =>
      unwrap(
        await api.PUT("/action-items/{action_item_id}/done", {
          params: { path: { action_item_id: input.id } },
          body: { done: input.done },
        }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tasksKey });

      return queryClient.invalidateQueries({ queryKey: ["meetings", "detail"] });
    },
  });
}

// The words the app shows for each status, in one place.
export const STATUS_LABEL: Record<MeetingStatus, string> = {
  waiting_for_audio: "Waiting for audio",
  processing: "Processing",
  done: "Done",
  failed: "Failed",
};
