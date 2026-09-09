"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { TokenPair, User } from "./types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  hasHydrated: boolean;
  setSession: (tokens: TokenPair, user: User) => void;
  setAccessToken: (accessToken: string) => void;
  clear: () => void;
  setHasHydrated: (v: boolean) => void;
}

// MVP tradeoff: tokens live in localStorage (via zustand persist), not an
// httpOnly cookie. Simpler for a single-origin-ish dev setup and a
// portfolio demo; the real cost is XSS-exposure of the refresh token.
// Worth revisiting with httpOnly cookies + a BFF-style proxy if this ever
// needs production-grade hardening.
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hasHydrated: false,
      setSession: (tokens, user) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          user,
        }),
      setAccessToken: (accessToken) => set({ accessToken }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
      setHasHydrated: (v) => set({ hasHydrated: v }),
    }),
    {
      name: "hirelens-auth",
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
