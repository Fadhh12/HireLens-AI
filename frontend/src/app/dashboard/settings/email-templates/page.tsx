"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { BackButton } from "@/components/back-button";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { listEmailTemplates, updateEmailTemplate } from "@/lib/messaging/api";
import type { EmailTemplate, EmailTrigger } from "@/lib/messaging/types";

const TRIGGER_LABEL: Record<EmailTrigger, string> = {
  shortlisted: "Shortlisted",
  rejected: "Rejected",
  hired: "Hired",
  interview: "Undangan Interview",
};

const TRIGGER_ORDER: EmailTrigger[] = ["shortlisted", "rejected", "hired", "interview"];

export default function EmailTemplatesPage() {
  // Same scope as job scoring weights — HR configuration, admin/recruiter only.
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <EmailTemplatesContent />
    </RequireAuth>
  );
}

function EmailTemplatesContent() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listEmailTemplates()
      .then(setTemplates)
      .catch((err) => toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memuat template"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-ink-400 text-sm">Memuat...</p>;

  return (
    <div className="max-w-3xl space-y-6">
      <BackButton fallbackHref="/dashboard" />
      <div className="space-y-1">
        <h1>Template Email</h1>
        <p className="caption">
          Shortlisted/Rejected/Hired terkirim otomatis lewat Gmail saat status kandidat diubah. Undangan
          Interview terkirim otomatis saat interview dijadwalkan (menggantikan undangan Calendar bawaan).
          Placeholder yang tersedia: {"{{full_name}}"}, {"{{job_title}}"}, {"{{department}}"} (semua template),
          dan khusus Undangan Interview: {"{{scheduled_at}}"}, {"{{duration_minutes}}"}, {"{{meet_link}}"}.
        </p>
      </div>

      {TRIGGER_ORDER.map((trigger) => {
        const template = templates.find((t) => t.trigger === trigger);
        if (!template) return null;
        return <TemplateEditor key={trigger} template={template} onSaved={(updated) => {
          setTemplates((prev) => prev.map((t) => (t.trigger === updated.trigger ? updated : t)));
        }} />;
      })}
    </div>
  );
}

function TemplateEditor({ template, onSaved }: { template: EmailTemplate; onSaved: (t: EmailTemplate) => void }) {
  const [subject, setSubject] = useState(template.subject);
  const [body, setBody] = useState(template.body);
  const [saving, setSaving] = useState(false);

  const dirty = subject !== template.subject || body !== template.body;

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateEmailTemplate(template.trigger, { subject, body });
      onSaved(updated);
      toast.success(`Template ${TRIGGER_LABEL[template.trigger]} disimpan`);
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal menyimpan template");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="border-border bg-card space-y-3 rounded-lg border p-4">
      <h2>{TRIGGER_LABEL[template.trigger]}</h2>
      <div className="space-y-1.5">
        <Label htmlFor={`subject-${template.trigger}`}>Subjek</Label>
        <Input id={`subject-${template.trigger}`} value={subject} onChange={(e) => setSubject(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor={`body-${template.trigger}`}>Isi pesan</Label>
        <Textarea
          id={`body-${template.trigger}`}
          rows={8}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="font-mono text-sm"
        />
      </div>
      <Button onClick={handleSave} disabled={!dirty || saving} size="sm">
        {saving ? "Menyimpan..." : "Simpan Template"}
      </Button>
    </section>
  );
}
