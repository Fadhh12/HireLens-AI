"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/lib/auth/store";

export default function Home() {
  const router = useRouter();
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!hasHydrated) return;
    router.replace(accessToken ? "/dashboard" : "/login");
  }, [hasHydrated, accessToken, router]);

  return (
    <div className="text-ink-400 flex min-h-screen items-center justify-center text-sm">
      Memuat...
    </div>
  );
}
