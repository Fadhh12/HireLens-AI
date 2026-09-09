import { apiFetch } from "@/lib/api/client";
import type { ActivityLogEntry } from "./types";

export function listActivityLogs(params?: { action?: string }): Promise<ActivityLogEntry[]> {
  const query = params?.action ? `?action=${encodeURIComponent(params.action)}` : "";
  return apiFetch(`/activity-logs${query}`);
}
