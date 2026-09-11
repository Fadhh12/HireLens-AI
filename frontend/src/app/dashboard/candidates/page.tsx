"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { MATCH_LABEL_TEXT, MatchLabelBadge } from "@/components/candidates/match-label-badge";
import { ScoreRing } from "@/components/candidates/score-ring";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError } from "@/lib/api/client";
import { listAllCandidates } from "@/lib/candidates/api";
import type { CandidateGlobalListItem, CandidateStatus, MatchLabel } from "@/lib/candidates/types";

// Same status vocabulary/coloring as the per-job Ranking Dashboard
// (dashboard/jobs/[id]/candidates/page.tsx) — kept in sync deliberately,
// see that file's Task 6.3 note on why status never borrows the
// match-label success/warning/danger colors.
const STATUS_LABEL: Record<CandidateStatus, string> = {
  new: "Baru",
  screening: "Screening",
  shortlisted: "Shortlisted",
  interviewed: "Interviewed",
  hired: "Hired",
  rejected: "Rejected",
  needs_manual_review: "Perlu Ditinjau Manual",
};

const STATUS_BADGE: Record<CandidateStatus, string> = {
  new: "bg-muted text-ink-600",
  screening: "bg-secondary text-primary",
  shortlisted: "bg-secondary text-primary",
  interviewed: "bg-primary text-primary-foreground",
  hired: "bg-primary text-primary-foreground",
  rejected: "bg-ink-900/10 text-ink-900",
  needs_manual_review: "border border-ink-400 text-ink-900",
};

const LABEL_FILTERS: MatchLabel[] = ["strong_match", "consider", "not_a_fit"];

type SortKey = "applied_desc" | "score_desc" | "name_asc";

export default function GlobalCandidatesPage() {
  // Same role scope as the per-job Ranking Dashboard — cross-job view of
  // the same data, not new access.
  return (
    <RequireAuth allowedRoles={["admin", "recruiter", "hiring_manager"]}>
      <GlobalCandidatesContent />
    </RequireAuth>
  );
}

function GlobalCandidatesContent() {
  const [candidates, setCandidates] = useState<CandidateGlobalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [jobFilter, setJobFilter] = useState<string>("all");
  const [labelFilter, setLabelFilter] = useState<MatchLabel | "all">("all");
  const [statusFilter, setStatusFilter] = useState<CandidateStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("applied_desc");

  useEffect(() => {
    listAllCandidates()
      .then(setCandidates)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : "Gagal memuat data"))
      .finally(() => setLoading(false));
  }, []);

  const jobOptions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const c of candidates) seen.set(c.job_posting_id, c.job_title);
    return [...seen.entries()];
  }, [candidates]);

  const labelCounts = useMemo(() => {
    const counts: Record<MatchLabel, number> = { strong_match: 0, consider: 0, not_a_fit: 0 };
    for (const c of candidates) {
      if (c.label) counts[c.label] += 1;
    }
    return counts;
  }, [candidates]);

  const visible = useMemo(() => {
    let list = candidates;
    if (jobFilter !== "all") list = list.filter((c) => c.job_posting_id === jobFilter);
    if (labelFilter !== "all") list = list.filter((c) => c.label === labelFilter);
    if (statusFilter !== "all") list = list.filter((c) => c.status === statusFilter);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((c) => c.full_name.toLowerCase().includes(q));
    }

    const sorted = [...list];
    if (sortKey === "score_desc") {
      sorted.sort((a, b) => (b.final_score ?? -1) - (a.final_score ?? -1));
    } else if (sortKey === "applied_desc") {
      sorted.sort((a, b) => new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime());
    } else {
      sorted.sort((a, b) => a.full_name.localeCompare(b.full_name));
    }
    return sorted;
  }, [candidates, jobFilter, labelFilter, statusFilter, search, sortKey]);

  if (loading) return <p className="text-ink-400 text-sm">Memuat...</p>;
  if (error) {
    return <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">{error}</p>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h1>Kandidat</h1>
        <p className="caption">{candidates.length} kandidat di semua job</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterChip active={labelFilter === "all"} onClick={() => setLabelFilter("all")}>
          Semua ({candidates.length})
        </FilterChip>
        {LABEL_FILTERS.map((l) => (
          <FilterChip key={l} active={labelFilter === l} onClick={() => setLabelFilter(l)}>
            {MATCH_LABEL_TEXT[l]} ({labelCounts[l]})
          </FilterChip>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Cari nama kandidat..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select value={jobFilter} onValueChange={(v) => setJobFilter(v ?? "all")}>
          <SelectTrigger className="w-48">
            <SelectValue>
              {jobFilter === "all" ? "Semua job" : (jobOptions.find(([id]) => id === jobFilter)?.[1] ?? "Semua job")}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua job</SelectItem>
            {jobOptions.map(([id, title]) => (
              <SelectItem key={id} value={id}>
                {title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as CandidateStatus | "all")}>
          <SelectTrigger className="w-44">
            <SelectValue>{statusFilter === "all" ? "Semua status" : STATUS_LABEL[statusFilter]}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua status</SelectItem>
            {(Object.keys(STATUS_LABEL) as CandidateStatus[]).map((s) => (
              <SelectItem key={s} value={s}>
                {STATUS_LABEL[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sortKey} onValueChange={(v) => setSortKey(v as SortKey)}>
          <SelectTrigger className="w-48">
            <SelectValue>
              {sortKey === "score_desc" ? "Skor tertinggi" : sortKey === "applied_desc" ? "Terbaru apply" : "Nama A-Z"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="score_desc">Skor tertinggi</SelectItem>
            <SelectItem value="applied_desc">Terbaru apply</SelectItem>
            <SelectItem value="name_asc">Nama A-Z</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="border-border bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Kandidat</TableHead>
              <TableHead>Job</TableHead>
              <TableHead>Skor</TableHead>
              <TableHead>Label</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Tanggal Apply</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {visible.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-ink-400 text-center">
                  {candidates.length === 0 ? "Belum ada kandidat." : "Tidak ada kandidat yang cocok dengan filter."}
                </TableCell>
              </TableRow>
            )}
            {visible.map((c) => (
              <TableRow key={c.id} className="hover:bg-accent">
                <TableCell className="font-medium">{c.full_name}</TableCell>
                <TableCell>
                  <Link href={`/dashboard/jobs/${c.job_posting_id}/candidates`} className="hover:underline">
                    {c.job_title}
                  </Link>
                </TableCell>
                <TableCell>
                  {c.final_score !== null ? (
                    <div className="flex items-center gap-2.5">
                      <ScoreRing score={c.final_score} label={c.label} />
                      <span className="tabular-score">{c.final_score.toFixed(1)}</span>
                    </div>
                  ) : (
                    <span className="text-ink-400 animate-pulse">Memproses...</span>
                  )}
                </TableCell>
                <TableCell>{c.label && <MatchLabelBadge label={c.label} />}</TableCell>
                <TableCell>
                  <Badge className={STATUS_BADGE[c.status]}>{STATUS_LABEL[c.status]}</Badge>
                </TableCell>
                <TableCell className="text-ink-600">
                  {new Date(c.applied_at).toLocaleDateString("id-ID")}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    render={<Link href={`/dashboard/candidates/${c.id}`}>Lihat</Link>}
                    nativeButton={false}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-card text-ink-600 hover:bg-accent"
      }`}
    >
      {children}
    </button>
  );
}
