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
  experience_years?: ParsedField<number>;
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

/** GET /jobs/{id}/candidates denormalizes each candidate's latest score
 * in — the ranking table needs it without one request per row. */
export interface CandidateListItem extends Candidate {
  final_score: number | null;
  label: MatchLabel | null;
  score_computed_at: string | null;
}

export interface CandidateCreateResponse extends Candidate {
  duplicate_warning: boolean;
}

/** GET /candidates (cross-job) — CandidateListItem + the job's title,
 * since this list isn't scoped to one job's page anymore. */
export interface CandidateGlobalListItem extends CandidateListItem {
  job_title: string;
}

export type MatchLabel = "strong_match" | "consider" | "not_a_fit";
