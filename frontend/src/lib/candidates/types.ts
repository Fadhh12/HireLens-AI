// Mirrors backend/app/modules/candidates/model.py + schema.py.

export type CandidateStatus =
  | "new"
  | "screening"
  | "shortlisted"
  | "interviewed"
  | "hired"
  | "rejected"
  | "needs_manual_review";

export interface ParsedField<T> {
  value: T;
  verified: boolean;
}

export interface ParsedProfile {
  name?: ParsedField<string | null>;
  email?: ParsedField<string | null>;
  phone?: ParsedField<string | null>;
  education?: ParsedField<string[]>;
  experience?: ParsedField<string[]>;
  skills?: ParsedField<string[]>;
  certifications?: ParsedField<string[]>;
  raw_text_length?: number;
  warnings?: string[];
}

export interface Candidate {
  id: string;
  job_posting_id: string;
  full_name: string;
  email: string;
  phone: string;
  cv_file_url: string;
  certificate_urls: string[];
  parsed_profile: ParsedProfile | null;
  assessment_input: Record<string, unknown> | null;
  status: CandidateStatus;
  applied_at: string;
}

export interface CandidateCreateResponse extends Candidate {
  duplicate_warning: boolean;
}
