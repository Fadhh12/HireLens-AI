"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { JobForm } from "@/components/jobs/job-form";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { getJob } from "@/lib/jobs/api";
import type { JobPosting } from "@/lib/jobs/types";

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
    <div className="max-w-2xl space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1>{job.title}</h1>
        <Button
          variant="outline"
          render={<Link href={`/dashboard/jobs/${job.id}/candidates`}>Lihat Kandidat</Link>}
          nativeButton={false}
        />
      </div>
      <JobForm initialJob={job} />
    </div>
  );
}
