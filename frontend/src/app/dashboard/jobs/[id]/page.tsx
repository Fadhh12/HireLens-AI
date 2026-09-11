"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { BackButton } from "@/components/back-button";
import { DonutChart } from "@/components/charts/donut-chart";
import { JobForm } from "@/components/jobs/job-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { listCandidates } from "@/lib/candidates/api";
import type { CandidateListItem, MatchLabel } from "@/lib/candidates/types";
import { getJob } from "@/lib/jobs/api";
import type { JobLevel, JobPosting, JobStatus } from "@/lib/jobs/types";

const LEVEL_LABEL: Record<JobLevel, string> = {
  junior: "Junior",
  mid: "Mid",
  senior: "Senior",
};

const STATUS_LABEL: Record<JobStatus, string> = {
  draft: "Draft",
  active: "Aktif",
  closed: "Closed",
};

// Same convention as jobs/page.tsx — success/warning/danger stay reserved
// for the candidate match label only (design system §2.1).
const STATUS_BADGE: Record<JobStatus, string> = {
  draft: "bg-muted text-ink-600",
  active: "bg-secondary text-primary",
  closed: "bg-ink-900/10 text-ink-900",
};

const LABEL_DONUT_COLOR: Record<MatchLabel, string> = {
  strong_match: "--success-700",
  consider: "--warning-700",
  not_a_fit: "--danger-700",
};

const LABEL_TEXT: Record<MatchLabel, string> = {
  strong_match: "Strong Match",
  consider: "Consider",
  not_a_fit: "Not a Fit",
};

export default function JobDetailPage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <JobDetailContent />
    </RequireAuth>
  );
}

function JobDetailContent() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<JobPosting | null>(null);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getJob(params.id)
      .then(setJob)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : "Gagal memuat job posting"))
      .finally(() => setLoading(false));
    // Best-effort — the job page shouldn't break if this side panel fetch fails.
    listCandidates(params.id)
      .then(setCandidates)
      .catch(() => setCandidates([]));
  }, [params.id]);

  if (loading) {
    return <p className="text-ink-400 text-sm">Memuat...</p>;
  }

  if (error || !job) {
    return (
      <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">
        {error ?? "Job posting tidak ditemukan"}
      </p>
    );
  }

  const labelCounts: Record<MatchLabel, number> = { strong_match: 0, consider: 0, not_a_fit: 0 };
  for (const c of candidates) {
    if (c.label) labelCounts[c.label] += 1;
  }
  const labeledTotal = labelCounts.strong_match + labelCounts.consider + labelCounts.not_a_fit;

  return (
    <div className="max-w-6xl space-y-6">
      <BackButton fallbackHref="/dashboard/jobs" />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2.5">
          <h1>{job.title}</h1>
          <Badge className={STATUS_BADGE[job.status]}>{STATUS_LABEL[job.status]}</Badge>
        </div>
        <Button
          variant="outline"
          render={<Link href={`/dashboard/jobs/${job.id}/candidates`}>Lihat Kandidat</Link>}
          nativeButton={false}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.7fr_1fr]">
        <JobForm initialJob={job} />

        <aside className="space-y-4">
          <section className="border-border bg-card space-y-3 rounded-lg border p-4">
            <h2>Info Lowongan</h2>
            <dl className="divide-border divide-y text-sm">
              <InfoRow label="Department" value={job.department} />
              <InfoRow label="Level" value={LEVEL_LABEL[job.level]} />
              <InfoRow label="Pengalaman minimum" value={`${job.min_experience_years} tahun`} />
              <InfoRow label="Tanggal dibuat" value={new Date(job.created_at).toLocaleDateString("id-ID")} />
            </dl>
          </section>

          <section className="border-border bg-card space-y-3 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <h2>Kandidat</h2>
              <span className="tabular-score text-sm">{candidates.length}</span>
            </div>
            {labeledTotal === 0 ? (
              <p className="text-ink-400 text-sm">Belum ada kandidat ternilai untuk job ini.</p>
            ) : (
              <div className="flex items-center gap-4">
                <DonutChart
                  size={104}
                  strokeWidth={14}
                  centerValue={String(labeledTotal)}
                  centerLabel="ternilai"
                  segments={(Object.keys(labelCounts) as MatchLabel[]).map((l) => ({
                    label: LABEL_TEXT[l],
                    value: labelCounts[l],
                    colorVar: LABEL_DONUT_COLOR[l],
                  }))}
                />
                <ul className="space-y-1.5 text-sm">
                  {(Object.keys(labelCounts) as MatchLabel[]).map((l) => (
                    <li key={l} className="flex items-center gap-1.5">
                      <span
                        className="size-2 shrink-0 rounded-full"
                        style={{ backgroundColor: `var(${LABEL_DONUT_COLOR[l]})` }}
                      />
                      <span className="text-ink-600">{LABEL_TEXT[l]}</span>
                      <span className="tabular-score ml-auto pl-3">{labelCounts[l]}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              render={<Link href={`/dashboard/jobs/${job.id}/candidates`}>Lihat semua kandidat</Link>}
              nativeButton={false}
            />
          </section>
        </aside>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 first:pt-0 last:pb-0">
      <span className="text-ink-600">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
