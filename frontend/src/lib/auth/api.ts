import { apiFetch } from "@/lib/api/client";

import type { TokenPair, User } from "./types";

export function login(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/login", {
    method: "POST",
    body: { email, password },
    skipAuth: true,
  });
}

export function fetchMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}
