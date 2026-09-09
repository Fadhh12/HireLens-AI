"use client";

import { useAuthStore } from "@/lib/auth/store";

export default function DashboardOverviewPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-2">
      <h1>Selamat datang, {user?.name?.split(" ")[0]}</h1>
      <p className="text-ink-600 max-w-xl text-sm">
        Ini halaman ringkasan sementara — metrik job aktif, kandidat baru, dan
        distribusi label kecocokan (UI/UX Layar 2) menyusul di Fase 5 setelah
        modul job posting &amp; matching engine ada datanya.
      </p>
    </div>
  );
}
