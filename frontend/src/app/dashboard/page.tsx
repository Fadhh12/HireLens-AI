"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MATCH_LABEL_TEXT } from "@/components/candidates/match-label-badge";
import { DonutChart } from "@/components/charts/donut-chart";
import { listCandidates } from "@/lib/candidates/api";
import type { MatchLabel } from "@/lib/candidates/types";
import { useAuthStore } from "@/lib/auth/store";
import { listJobs } from "@/lib/jobs/api";
import type { JobPosting } from "@/lib/jobs/types";

const LABEL_BAR_CLASS: Record<MatchLabel, string> = {
  strong_match: "bg-success-700",
  consider: "bg-warning-700",
  not_a_fit: "bg-danger-700",
};

const LABEL_DONUT_COLOR: Record<MatchLabel, string> = {
  strong_match: "--success-700",
  consider: "--warning-700",
  not_a_fit: "--danger-700",
};

interface JobWithCount extends JobPosting {
  candidateCount: number;
}

export default function DashboardOverviewPage() {
  const user = useAuthStore((s) => s.user);
  const [jobs, setJobs] = useState<JobWithCount[]>([]);
  const [labelCounts, setLabelCounts] = useState<Record<MatchLabel, number>>({
    strong_match: 0,
    consider: 0,
    not_a_fit: 0,
  });
  const [newThisWeek, setNewThisWeek] = useState(0);
  const [loading, setLoading] = useState(true);

  // UI/UX Flow §3 Screen 2: Admin, Recruiter, Hiring Manager (Task 6.3 finding —
  // hiring_manager was missing, leaving them with a blank overview and no way to
  // reach the ranking dashboard from here).
  const canSeeJobs = user?.role === "admin" || user?.role === "recruiter" || user?.role === "hiring_manager";

  useEffect(() => {
    if (!canSeeJobs) {
      setLoading(false);
      return;
    }
    listJobs("active")
      .then(async (activeJobs) => {
        const counts: Record<MatchLabel, number> = { strong_match: 0, consider: 0, not_a_fit: 0 };
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        let recentCount = 0;

        const withCounts = await Promise.all(
          activeJobs.map(async (job) => {
            const candidates = await listCandidates(job.id).catch(() => []);
            for (const c of candidates) {
              if (c.label) counts[c.label] += 1;
              if (new Date(c.applied_at).getTime() >= weekAgo) recentCount += 1;
            }
            return { ...job, candidateCount: candidates.length };
          })
        );
        setJobs(withCounts);
        setLabelCounts(counts);
        setNewThisWeek(recentCount);
      })
      .finally(() => setLoading(false));
  }, [canSeeJobs]);

  const totalLabeled = labelCounts.strong_match + labelCounts.consider + labelCounts.not_a_fit;

  return (
    <div className="space-y-6">
      <h1>Selamat datang, {user?.name?.split(" ")[0]}</h1>

      {!canSeeJobs && (
        <p className="text-ink-600 max-w-xl text-sm">
          Ringkasan job & kandidat tersedia untuk role Admin/Recruiter.
        </p>
      )}

      {canSeeJobs && !loading && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <MetricCard label="Job Aktif" value={jobs.length} />
            <MetricCard label="Kandidat Baru (7 hari)" value={newThisWeek} />
            <MetricCard label="Total Kandidat Ternilai" value={totalLabeled} />
          </div>

          {totalLabeled > 0 && (
            <section className="border-border bg-card space-y-4 rounded-lg border p-4">
              <h2>Distribusi Label Kecocokan</h2>
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
                <DonutChart
                  centerValue={String(totalLabeled)}
                  centerLabel="kandidat"
                  segments={(Object.keys(labelCounts) as MatchLabel[]).map((label) => ({
                    label: MATCH_LABEL_TEXT[label],
                    value: labelCounts[label],
                    colorVar: LABEL_DONUT_COLOR[label],
                  }))}
                />
                <div className="w-full flex-1 space-y-3">
                  {(Object.keys(labelCounts) as MatchLabel[]).map((label) => {
                    const pct = (labelCounts[label] / totalLabeled) * 100;
                    return (
                      <div key={label} className="space-y-1">
                        <div className="flex items-center gap-2 text-sm">
                          <span
                            className="size-2.5 shrink-0 rounded-full"
                            style={{ backgroundColor: `var(${LABEL_DONUT_COLOR[label]})` }}
                          />
                          <span className="flex-1">{MATCH_LABEL_TEXT[label]}</span>
                          <span className="tabular-score">{labelCounts[label]}</span>
                          <span className="caption w-12 text-right">{pct.toFixed(0)}%</span>
                        </div>
                        <div className="bg-muted h-2 overflow-hidden rounded-full">
                          <div className={`h-full ${LABEL_BAR_CLASS[label]}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>
          )}

          <section className="space-y-2">
            <h2>Job Aktif</h2>
            <div className="border-border bg-card divide-border divide-y rounded-lg border">
              {jobs.length === 0 && <p className="text-ink-400 p-4 text-sm">Belum ada job aktif.</p>}
              {jobs.map((job) => {
                const maxCount = Math.max(...jobs.map((j) => j.candidateCount), 1);
                return (
                  <Link
                    key={job.id}
                    href={`/dashboard/jobs/${job.id}/candidates`}
                    className="hover:bg-accent flex items-center gap-4 p-4 text-sm"
                  >
                    <span className="min-w-0 flex-1 truncate font-medium">{job.title}</span>
                    <div className="bg-muted hidden h-1.5 w-28 shrink-0 overflow-hidden rounded-full sm:block">
                      <div
                        className="bg-primary h-full"
                        style={{ width: `${(job.candidateCount / maxCount) * 100}%` }}
                      />
                    </div>
                    <span className="caption w-20 shrink-0 text-right">{job.candidateCount} kandidat</span>
                  </Link>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-border bg-card rounded-lg border p-4">
      <p className="caption">{label}</p>
      <p className="tabular-score text-2xl">{value}</p>
    </div>
  );
}
