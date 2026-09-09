import { apiFetch } from "@/lib/api/client";

import type { CandidateScore } from "./types";

export function getCandidateScore(candidateId: string): Promise<CandidateScore> {
  return apiFetch<CandidateScore>(`/candidates/${candidateId}/score`);
}

export function triggerScore(candidateId: string): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>(`/candidates/${candidateId}/score`, { method: "POST" });
}
