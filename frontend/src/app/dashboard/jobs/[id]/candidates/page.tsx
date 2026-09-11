"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { BackButton } from "@/components/back-button";
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
import { listCandidates } from "@/lib/candidates/api";
import type { CandidateListItem, CandidateStatus, MatchLabel } from "@/lib/candidates/types";
import { getJob } from "@/lib/jobs/api";
import type { JobPosting } from "@/lib/jobs/types";
import { useAuthStore } from "@/lib/auth/store";

const STATUS_LABEL: Record<CandidateStatus, string> = {
  new: "Baru",
  screening: "Screening",
  shortlisted: "Shortlisted",
  interviewed: "Interviewed",
  hired: "Hired",
  rejected: "Rejected",
  needs_manual_review: "Perlu Ditinjau Manual",
};

// Design system §2.1: success/warning/danger are reserved for the match label
// (Strong Match/Consider/Not a Fit) ONLY, never for other UI elements — pipeline
// status here reads off the ink/primary scale instead so the two never collide
// (Task 6.3 finding: this used to borrow success/warning/danger, same pills as
// the match label sitting right next to it in the ranking table).
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

type SortKey = "score_desc" | "applied_desc" | "name_asc";

export default function RankingDashboardPage() {
  // UI/UX Flow §3 Screen 6: Recruiter, Hiring Manager (Task 6.3 finding — this
  // was wrongly locked to admin/recruiter only, blocking Flow C review).
  return (
    <RequireAuth allowedRoles={["admin", "recruiter", "hiring_manager"]}>
      <RankingDashboardContent />
    </RequireAuth>
  );
}

function RankingDashboardContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const role = useAuthStore((s) => s.user?.role);
  const canIntake = role === "admin" || role === "recruiter"; // matches candidates/new's own RequireAuth
  const [job, setJob] = useState<JobPosting | null>(null);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [labelFilter, setLabelFilter] = useState<MatchLabel | "all">("all");
  const [statusFilter, setStatusFilter] = useState<CandidateStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("score_desc");
  const [selected, setSelected] = useState<string[]>([]);

  function toggleSelect(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  }

  useEffect(() => {
    Promise.all([getJob(params.id), listCandidates(params.id)])
      .then(([j, c]) => {
        setJob(j);
        setCandidates(c);
      })
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : "Gagal memuat data"))
      .finally(() => setLoading(false));
  }, [params.id]);

  const labelCounts = useMemo(() => {
    const counts: Record<MatchLabel, number> = { strong_match: 0, consider: 0, not_a_fit: 0 };
    for (const c of candidates) {
      if (c.label) counts[c.label] += 1;
    }
    return counts;
  }, [candidates]);

  const visible = useMemo(() => {
    let list = candidates;
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
  }, [candidates, labelFilter, statusFilter, search, sortKey]);

  if (loading) return <p className="text-ink-400 text-sm">Memuat...</p>;
  if (error || !job) {
    return <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">{error}</p>;
  }

  return (
    <div className="space-y-4">
      <BackButton fallbackHref="/dashboard/jobs" />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1>{job.title}</h1>
          <p className="caption">{candidates.length} kandidat total</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            disabled={selected.length < 2}
            onClick={() =>
              router.push(`/dashboard/jobs/${job.id}/candidates/compare?ids=${selected.join(",")}`)
            }
          >
            Bandingkan ({selected.length})
          </Button>
          {canIntake && (
            <Button
              render={<Link href={`/dashboard/jobs/${job.id}/candidates/new`}>+ Tambah Kandidat</Link>}
              nativeButton={false}
            />
          )}
        </div>
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
              <TableHead className="w-8"></TableHead>
              <TableHead>Kandidat</TableHead>
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
                  {candidates.length === 0 ? "Belum ada kandidat untuk job ini." : "Tidak ada kandidat yang cocok dengan filter."}
                </TableCell>
              </TableRow>
            )}
            {visible.map((c) => (
              <TableRow key={c.id} className="hover:bg-accent">
                <TableCell>
                  <input
                    type="checkbox"
                    checked={selected.includes(c.id)}
                    onChange={() => toggleSelect(c.id)}
                    disabled={!selected.includes(c.id) && selected.length >= 3}
                    aria-label={`Pilih ${c.full_name} untuk dibandingkan`}
                  />
                </TableCell>
                <TableCell className="font-medium">{c.full_name}</TableCell>
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
