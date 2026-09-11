import { apiFetch } from "@/lib/api/client";

import type { GoogleConnectionStatus, InterviewSchedule, InterviewScheduleInput } from "./types";

export function getGoogleConnectionStatus(): Promise<GoogleConnectionStatus> {
  return apiFetch<GoogleConnectionStatus>("/integrations/google/status");
}

/** Returns the Google consent URL — caller does `window.location.href = url`
 * (a plain link/redirect can't carry the Authorization header this needs). */
export function getGoogleConnectUrl(returnTo: string): Promise<{ authorize_url: string }> {
  return apiFetch<{ authorize_url: string }>(
    `/integrations/google/connect?return_to=${encodeURIComponent(returnTo)}`
  );
}

export function disconnectGoogle(): Promise<void> {
  return apiFetch<void>("/integrations/google", { method: "DELETE" });
}

export function scheduleInterview(candidateId: string, input: InterviewScheduleInput): Promise<InterviewSchedule> {
  return apiFetch<InterviewSchedule>(`/candidates/${candidateId}/interview-schedule`, {
    method: "POST",
    body: input,
  });
}

export function listInterviewSchedules(candidateId: string): Promise<InterviewSchedule[]> {
  return apiFetch<InterviewSchedule[]>(`/candidates/${candidateId}/interview-schedule`);
}
