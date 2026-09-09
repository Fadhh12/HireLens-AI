"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/lib/auth/store";
import type { UserRole } from "@/lib/auth/types";

interface RequireAuthProps {
  children: React.ReactNode;
  /** If given, redirect to /dashboard when the current user's role isn't in this list. */
  allowedRoles?: UserRole[];
}

export function RequireAuth({ children, allowedRoles }: RequireAuthProps) {
  const router = useRouter();
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    if (allowedRoles && user && !allowedRoles.includes(user.role)) {
      router.replace("/dashboard");
    }
  }, [hasHydrated, accessToken, user, allowedRoles, router]);

  if (!hasHydrated || !accessToken) {
    return (
      <div className="text-ink-400 flex min-h-screen items-center justify-center text-sm">
        Memuat...
      </div>
    );
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}
