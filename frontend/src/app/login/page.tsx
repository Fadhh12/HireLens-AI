"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { fetchMe, login } from "@/lib/auth/api";
import { useAuthStore } from "@/lib/auth/store";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Logomark } from "@/components/logomark";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await login(email, password);
      // Stash the access token immediately so the /auth/me call below is authenticated.
      useAuthStore.setState({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const user = await fetchMe();
      setSession(tokens, user);
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        // FR-1.4 / UI/UX Layar 1: surface the backend's specific message
        // ("Email atau kata sandi salah" or the lockout countdown), never a
        // generic "something went wrong".
        setError(typeof err.detail === "string" ? err.detail : "Gagal login, coba lagi.");
      } else {
        setError("Tidak bisa terhubung ke server. Coba lagi.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="border-border bg-card w-full max-w-sm rounded-xl border p-8 shadow-sm">
        <div className="mb-1 flex items-center gap-2.5">
          <Logomark />
          <h1>HireLens AI</h1>
        </div>
        <p className="caption mb-6">Masuk untuk melanjutkan ke dashboard.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nama@perusahaan.com"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password">Kata sandi</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Memproses..." : "Masuk"}
          </Button>
        </form>
      </div>
    </main>
  );
}
