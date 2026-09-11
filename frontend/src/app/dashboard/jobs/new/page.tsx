"use client";

import { RequireAuth } from "@/components/require-auth";
import { BackButton } from "@/components/back-button";
import { JobForm } from "@/components/jobs/job-form";

export default function NewJobPage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <div className="max-w-2xl space-y-4">
        <BackButton fallbackHref="/dashboard/jobs" />
        <h1>Buat Job Baru</h1>
        <JobForm />
      </div>
    </RequireAuth>
  );
}
