export interface ActivityLogEntry {
  id: string;
  candidate_id: string | null;
  actor_id: string;
  actor_name: string;
  action: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}
