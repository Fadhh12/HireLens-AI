// Mirrors backend/app/modules/jobs/model.py + schema.py.

export type JobLevel = "junior" | "mid" | "senior";
export type JobStatus = "draft" | "active" | "closed";

export interface JobPosting {
  id: string;
  title: string;
  department: string;
  description: string;
  required_skills: string[];
  nice_to_have_skills: string[];
  min_experience_years: number;
  level: JobLevel;
  weight_skill_fit: number;
  weight_experience_fit: number;
  weight_values_fit: number;
  status: JobStatus;
  created_by: string;
  created_at: string;
}

export interface JobPostingInput {
  title: string;
  department: string;
  description: string;
  required_skills: string[];
  nice_to_have_skills: string[];
  min_experience_years: number;
  level: JobLevel;
  weight_skill_fit: number;
  weight_experience_fit: number;
  weight_values_fit: number;
  status: JobStatus;
}
