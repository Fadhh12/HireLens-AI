import { apiFetch } from "@/lib/api/client";

import type { JobPosting, JobPostingInput, JobStatus } from "./types";

export function listJobs(status?: JobStatus): Promise<JobPosting[]> {
  const query = status ? `?status=${status}` : "";
  return apiFetch<JobPosting[]>(`/jobs${query}`);
}

export function getJob(id: string): Promise<JobPosting> {
  return apiFetch<JobPosting>(`/jobs/${id}`);
}

export function createJob(input: JobPostingInput): Promise<JobPosting> {
  return apiFetch<JobPosting>("/jobs", { method: "POST", body: input });
}

export function updateJob(id: string, input: Partial<JobPostingInput>): Promise<JobPosting> {
  return apiFetch<JobPosting>(`/jobs/${id}`, { method: "PATCH", body: input });
}

export function closeJob(id: string): Promise<JobPosting> {
  return apiFetch<JobPosting>(`/jobs/${id}/close`, { method: "POST" });
}
