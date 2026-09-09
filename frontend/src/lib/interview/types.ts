export interface InterviewGuide {
  id: string;
  candidate_id: string;
  technical_questions: string[];
  behavioral_questions: string[];
  risk_areas: string[];
  version: number;
  is_final: boolean;
  created_by: string;
  created_at: string;
}
