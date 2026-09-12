// Mirrors backend/app/modules/messaging/schema.py + model.py.

export type EmailTrigger = "shortlisted" | "rejected" | "hired";

export interface EmailTemplate {
  trigger: EmailTrigger;
  subject: string;
  body: string;
  updated_at: string;
}

export interface EmailTemplateInput {
  subject: string;
  body: string;
}

export interface CandidateEmail {
  id: string;
  candidate_id: string;
  sent_by: string;
  trigger: EmailTrigger;
  subject: string;
  body: string;
  attachment_filename: string | null;
  has_reply: boolean;
  reply_snippet: string | null;
  reply_detected_at: string | null;
  sent_at: string;
}
