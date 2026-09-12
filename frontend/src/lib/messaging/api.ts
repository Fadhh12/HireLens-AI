import { apiFetch } from "@/lib/api/client";

import type { CandidateEmail, EmailTemplate, EmailTemplateInput, EmailTrigger } from "./types";

export function listEmailTemplates(): Promise<EmailTemplate[]> {
  return apiFetch<EmailTemplate[]>("/email-templates");
}

export function updateEmailTemplate(trigger: EmailTrigger, input: EmailTemplateInput): Promise<EmailTemplate> {
  return apiFetch<EmailTemplate>(`/email-templates/${trigger}`, { method: "PATCH", body: input });
}

export function pollEmailReplies(): Promise<{ new_replies: number }> {
  return apiFetch<{ new_replies: number }>("/email-templates/poll-replies", { method: "POST" });
}

export function listCandidateEmails(candidateId: string): Promise<CandidateEmail[]> {
  return apiFetch<CandidateEmail[]>(`/candidates/${candidateId}/emails`);
}

/** multipart — `attachment` optional (assessment PDF / signed contract). */
export function sendStatusEmail(
  candidateId: string,
  trigger: EmailTrigger,
  attachment?: File
): Promise<CandidateEmail> {
  const form = new FormData();
  form.set("trigger", trigger);
  if (attachment) form.set("attachment", attachment);
  return apiFetch<CandidateEmail>(`/candidates/${candidateId}/send-email`, {
    method: "POST",
    body: form,
  });
}
