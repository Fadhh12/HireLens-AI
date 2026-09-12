import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthStore } from "@/lib/auth/store";

import type {
  Candidate,
  CandidateCreateResponse,
  CandidateGlobalListItem,
  CandidateListItem,
  CandidateStatus,
} from "./types";

export interface IntakeCandidateInput {
  full_name: string;
  email: string;
  phone: string;
  cv_file: File;
  certificate_files?: File[];
  assessment_input?: Record<string, unknown>;
  photo_file?: File;
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
  if (input.assessment_input) {
    form.set("assessment_input", JSON.stringify(input.assessment_input));
  }
  if (input.photo_file) {
    form.set("photo", input.photo_file);
  }

  return apiFetch<CandidateCreateResponse>(`/jobs/${jobId}/candidates`, {
    method: "POST",
    body: form,
  });
}

export function listCandidates(jobId: string): Promise<CandidateListItem[]> {
  return apiFetch<CandidateListItem[]>(`/jobs/${jobId}/candidates`);
}

/** GET /candidates (cross-job) — the "Kandidat" sidebar screen. */
export function listAllCandidates(): Promise<CandidateGlobalListItem[]> {
  return apiFetch<CandidateGlobalListItem[]>(`/candidates`);
}

export function getCandidate(id: string): Promise<Candidate> {
  return apiFetch<Candidate>(`/candidates/${id}`);
}

export function updateCandidate(
  id: string,
  input: Partial<Pick<Candidate, "full_name" | "email" | "phone" | "parsed_profile" | "assessment_input">>
): Promise<Candidate> {
  return apiFetch<Candidate>(`/candidates/${id}`, { method: "PATCH", body: input });
}

export function updateCandidateStatus(id: string, status: CandidateStatus, reason: string): Promise<Candidate> {
  return apiFetch<Candidate>(`/candidates/${id}/status`, { method: "PATCH", body: { status, reason } });
}

/** FR-9: PDF isn't JSON, so this bypasses apiFetch and handles the
 * Authorization header + blob response directly. */
export async function downloadCandidateReportPdf(id: string, filename: string): Promise<void> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const token = useAuthStore.getState().accessToken;
  const res = await fetch(`${API_URL}/candidates/${id}/report/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new ApiError(res.status, "Gagal mengekspor laporan PDF");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
