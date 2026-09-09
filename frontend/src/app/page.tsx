import { Button } from "@/components/ui/button";

const statusBadges = [
  { label: "Strong Match", fg: "text-success-700", bg: "bg-success-100" },
  { label: "Consider", fg: "text-warning-700", bg: "bg-warning-100" },
  { label: "Not a Fit", fg: "text-danger-700", bg: "bg-danger-100" },
] as const;

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-6 py-16">
      <div className="space-y-2">
        <p className="caption uppercase tracking-wide">Phase 0 — scaffold</p>
        <h1>HireLens AI</h1>
        <p className="text-ink-600 max-w-xl text-sm">
          Platform screening & pencocokan kandidat berbasis AI — parsing CV,
          skor yang bisa diaudit, dan persiapan wawancara. Halaman ini cuma
          konfirmasi visual bahwa design tokens (warna, tipografi, radius)
          sudah terpasang sebelum layar sesungguhnya mulai dibangun.
        </p>
      </div>

      <div className="border-border bg-card flex flex-wrap items-center gap-3 rounded-lg border p-4">
        {statusBadges.map((s) => (
          <span
            key={s.label}
            className={`rounded-full px-3 py-1 text-xs font-medium ${s.fg} ${s.bg}`}
          >
            {s.label}
          </span>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button>Primary action</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
      </div>
    </main>
  );
}
