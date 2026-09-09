"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { JobForm } from "@/components/jobs/job-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import type { Candidate, CandidateStatus } from "@/lib/candidates/types";
import { getJob } from "@/lib/jobs/api";
import type { JobPosting } from "@/lib/jobs/types";

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
  shortlisted: "bg-success-100 text-success-700",
  interviewed: "bg-secondary text-primary",
  hired: "bg-success-100 text-success-700",
  rejected: "bg-danger-100 text-danger-700",
  needs_manual_review: "bg-warning-100 text-warning-700",
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
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getJob(params.id)
      .then(setJob)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : "Gagal memuat job posting"))
      .finally(() => setLoading(false));
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

  return (
    <div className="max-w-2xl space-y-10">
      <div className="space-y-4">
        <h1>{job.title}</h1>
        <JobForm initialJob={job} />
      </div>

      <CandidatesSection jobId={job.id} />
    </div>
  );
}

function CandidatesSection({ jobId }: { jobId: string }) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listCandidates(jobId)
      .then(setCandidates)
      .finally(() => setLoading(false));
  }, [jobId]);

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2>Kandidat ({candidates.length})</h2>
        <Button
          size="sm"
          render={<Link href={`/dashboard/jobs/${jobId}/candidates/new`}>+ Tambah Kandidat</Link>}
          nativeButton={false}
        />
      </div>

      <div className="border-border bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nama</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Tanggal Apply</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={4} className="text-ink-400 text-center">
                  Memuat...
                </TableCell>
              </TableRow>
            )}
            {!loading && candidates.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-ink-400 text-center">
                  Belum ada kandidat untuk job ini.
                </TableCell>
              </TableRow>
            )}
            {candidates.map((c) => (
              <TableRow key={c.id} className="hover:bg-accent">
                <TableCell className="font-medium">
                  <Link href={`/dashboard/candidates/${c.id}`}>{c.full_name}</Link>
                </TableCell>
                <TableCell className="text-ink-600">{c.email}</TableCell>
                <TableCell>
                  <Badge className={STATUS_BADGE[c.status]}>{STATUS_LABEL[c.status]}</Badge>
                </TableCell>
                <TableCell className="text-ink-600">
                  {new Date(c.applied_at).toLocaleDateString("id-ID")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
