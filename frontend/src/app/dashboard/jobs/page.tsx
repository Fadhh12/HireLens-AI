"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/require-auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { listJobs } from "@/lib/jobs/api";
import type { JobPosting, JobStatus } from "@/lib/jobs/types";

const STATUS_LABEL: Record<JobStatus, string> = {
  draft: "Draft",
  active: "Aktif",
  closed: "Closed",
};

const STATUS_BADGE: Record<JobStatus, string> = {
  draft: "bg-muted text-ink-600",
  active: "bg-success-100 text-success-700",
  closed: "bg-danger-100 text-danger-700",
};

type StatusFilter = JobStatus | "all";

export default function JobsListPage() {
  return (
    <RequireAuth>
      <JobsListContent />
    </RequireAuth>
  );
}

function JobsListContent() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    setLoading(true);
    listJobs(statusFilter === "all" ? undefined : statusFilter)
      .then(setJobs)
      .catch((err) => toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memuat lowongan"))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1>Lowongan</h1>
          <p className="caption">Kelola job posting & kriteria scoring (FR-2).</p>
        </div>
        <Button
          render={<Link href="/dashboard/jobs/new">+ Buat Job Baru</Link>}
          nativeButton={false}
        />
      </div>

      <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as StatusFilter)}>
        <SelectTrigger className="w-44">
          <SelectValue>{statusFilter === "all" ? "Semua status" : STATUS_LABEL[statusFilter]}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Semua status</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="active">Aktif</SelectItem>
          <SelectItem value="closed">Closed</SelectItem>
        </SelectContent>
      </Select>

      <div className="border-border bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Judul Job</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Level</TableHead>
              <TableHead>Tanggal Dibuat</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={5} className="text-ink-400 text-center">
                  Memuat...
                </TableCell>
              </TableRow>
            )}
            {!loading && jobs.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-ink-400 text-center">
                  Belum ada lowongan di kategori ini.
                </TableCell>
              </TableRow>
            )}
            {jobs.map((job) => (
              <TableRow key={job.id} className="hover:bg-accent cursor-pointer">
                <TableCell className="font-medium">
                  <Link href={`/dashboard/jobs/${job.id}`} className="block">
                    {job.title}
                  </Link>
                </TableCell>
                <TableCell className="text-ink-600">{job.department}</TableCell>
                <TableCell>
                  <Badge className={STATUS_BADGE[job.status]}>{STATUS_LABEL[job.status]}</Badge>
                </TableCell>
                <TableCell className="text-ink-600 capitalize">{job.level}</TableCell>
                <TableCell className="text-ink-600">
                  {new Date(job.created_at).toLocaleDateString("id-ID")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
