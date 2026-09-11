// Mirrors backend/app/modules/scheduling/schema.py.

export interface GoogleConnectionStatus {
  connected: boolean;
  google_email: string | null;
}

export interface InterviewScheduleInput {
  /** ISO 8601 with timezone offset. */
  scheduled_at: string;
  duration_minutes: number;
}

export interface InterviewSchedule {
  id: string;
  candidate_id: string;
  scheduled_by: string;
  scheduled_at: string;
  duration_minutes: number;
  meet_link: string;
  calendar_html_link: string | null;
  created_at: string;
}
