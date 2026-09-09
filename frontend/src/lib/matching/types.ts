import type { MatchLabel } from "@/lib/candidates/types";

export interface ScoreComponent {
  score: number | null;
  weight: number;
  [key: string]: unknown;
}

export interface ScoreBreakdown {
  skill_fit: ScoreComponent & {
    matched_required: string[];
    missing_required: string[];
    matched_nice_to_have: string[];
  };
  experience_fit: ScoreComponent & { candidate_years: number; required_years: number };
  values_fit: ScoreComponent & { note?: string; mbti?: string | null };
  candidate_summary: string | null;
  inputs_snapshot?: Record<string, unknown>;
}

export interface CandidateScore {
  id: string;
  candidate_id: string;
  skill_fit_score: number;
  experience_fit_score: number;
  values_fit_score: number | null;
  final_score: number;
  label: MatchLabel;
  score_breakdown: ScoreBreakdown;
  model_version: string;
  computed_at: string;
}
