import { apiFetch } from "@/lib/api/client";

import type { Candidate, CandidateCreateResponse } from "./types";

export interface IntakeCandidateInput {
  full_name: string;
  email: string;
  phone: string;
  cv_file: File;
  certificate_files?: File[];
  assessment_input?: Record<string, unknown>;
}

export function intakeCandidate(
  jobId: string,
  input: IntakeCandidateInput
): Promise<CandidateCreateResponse> {
  const form = new FormData();
  form.set("full_name", input.full_name);
  form.set("email", input.email);
  form.set("phone", input.phone);
  form.set("cv_file", input.cv_file);
  for (const cert of input.certificate_files ?? []) {
    form.append("certificate_files", cert);
  }

  return apiFetch<CandidateCreateResponse>(`/jobs/${jobId}/candidates`, {
    method: "POST",
    body: form,
  });
}

export function listCandidates(jobId: string): Promise<Candidate[]> {
  return apiFetch<Candidate[]>(`/jobs/${jobId}/candidates`);
}

export function getCandidate(id: string): Promise<Candidate> {
  return apiFetch<Candidate>(`/candidates/${id}`);
}

export function updateCandidate(id: string, input: Partial<Pick<Candidate, "full_name" | "email" | "phone" | "parsed_profile" | "assessment_input">>): Promise<Candidate> {
  return apiFetch<Candidate>(`/candidates/${id}`, { method: "PATCH", body: input });
}
