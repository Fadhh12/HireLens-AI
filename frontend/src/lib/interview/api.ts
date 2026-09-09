import { apiFetch } from "@/lib/api/client";
import type { InterviewGuide } from "./types";

export function triggerGenerateGuide(candidateId: string): Promise<{ detail: string }> {
  return apiFetch(`/candidates/${candidateId}/interview-guide`, { method: "POST" });
}

export function getLatestGuide(candidateId: string): Promise<InterviewGuide> {
  return apiFetch(`/candidates/${candidateId}/interview-guide`);
}

export function listGuideVersions(candidateId: string): Promise<InterviewGuide[]> {
  return apiFetch(`/candidates/${candidateId}/interview-guide/versions`);
}

export function updateGuide(
  guideId: string,
  input: Partial<Pick<InterviewGuide, "technical_questions" | "behavioral_questions" | "risk_areas">>
): Promise<InterviewGuide> {
  return apiFetch(`/interview-guide/${guideId}`, { method: "PATCH", body: input });
}

export function finalizeGuide(guideId: string): Promise<InterviewGuide> {
  return apiFetch(`/interview-guide/${guideId}/finalize`, { method: "POST" });
}
