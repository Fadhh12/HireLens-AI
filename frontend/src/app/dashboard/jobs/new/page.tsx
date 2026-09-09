"use client";

import { RequireAuth } from "@/components/require-auth";
import { JobForm } from "@/components/jobs/job-form";

export default function NewJobPage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <div className="space-y-4">
        <h1>Buat Job Baru</h1>
        <JobForm />
      </div>
    </RequireAuth>
  );
}
