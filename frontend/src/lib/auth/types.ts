// Mirrors backend/app/modules/auth/model.py UserRole and schema.UserOut.

export type UserRole = "admin" | "recruiter" | "hiring_manager" | "interviewer";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
