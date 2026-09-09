import { apiFetch } from "@/lib/api/client";
import type { User, UserRole } from "@/lib/auth/types";

export interface CreateUserInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface UpdateUserInput {
  name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/users");
}

export function createUser(input: CreateUserInput): Promise<User> {
  return apiFetch<User>("/users", { method: "POST", body: input });
}

export function updateUser(id: string, input: UpdateUserInput): Promise<User> {
  return apiFetch<User>(`/users/${id}`, { method: "PATCH", body: input });
}
