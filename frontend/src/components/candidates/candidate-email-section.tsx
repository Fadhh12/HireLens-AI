"use client";

import { CheckCircle2, Paperclip } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { listCandidateEmails, sendStatusEmail } from "@/lib/messaging/api";
import type { CandidateEmail, EmailTrigger } from "@/lib/messaging/types";
import type { CandidateStatus } from "@/lib/candidates/types";

const TRIGGER_LABEL: Record<EmailTrigger, string> = {
  shortlisted: "Shortlisted",
  rejected: "Rejected",
  hired: "Hired",
  interview: "Undangan Interview",
};

const RESENDABLE: EmailTrigger[] = ["shortlisted", "rejected", "hired"];

/** Not in the original SDD — a later feature request: shortlisted/
 * rejected/hired auto-send a templated Gmail email on status change
 * (candidates/service.py's update_status). This section shows that
 * history and lets HR resend with an attachment (assessment PDF /
 * signed contract) — the automatic send never carries one. */
export function CandidateEmailSection({ candidateId, status }: { candidateId: string; status: CandidateStatus }) {
  const [emails, setEmails] = useState<CandidateEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function load() {
    listCandidateEmails(candidateId)
      .then(setEmails)
      .catch(() => {
        // Best-effort — rest of the candidate page still works without this section.
      })
      .finally(() => setLoading(false));
  }

  // Reload on status change too — that's exactly when update_status may
  // have auto-sent a new email server-side (see candidates/service.py).
  useEffect(load, [candidateId, status]);

  const canResend = RESENDABLE.includes(status as EmailTrigger);

  async function handleSend() {
    setSending(true);
    try {
      const file = fileInputRef.current?.files?.[0];
      const created = await sendStatusEmail(candidateId, status as EmailTrigger, file);
      setEmails((prev) => [created, ...prev]);
      if (fileInputRef.current) fileInputRef.current.value = "";
      toast.success("Email terkirim ke kandidat");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal mengirim email");
    } finally {
      setSending(false);
    }
  }

  if (loading) return null;
  if (emails.length === 0 && !canResend) return null;

  return (
    <section className="border-border bg-card space-y-3 rounded-lg border p-4">
      <h2>Riwayat Email</h2>

      {canResend && (
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="border-input max-w-[220px] rounded-lg border bg-transparent text-xs file:mr-2 file:h-full file:border-0 file:bg-transparent file:text-xs"
          />
          <Button variant="outline" size="sm" onClick={handleSend} disabled={sending}>
            {sending ? "Mengirim..." : `Kirim Email ${TRIGGER_LABEL[status as EmailTrigger]}`}
          </Button>
          <span className="caption">Lampiran PDF opsional (soal asesmen / kontrak).</span>
        </div>
      )}

      {emails.length > 0 && (
        <ul className="divide-border divide-y">
          {emails.map((email) => (
            <li key={email.id} className="space-y-1 py-2 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{email.subject}</span>
                <span className="caption">{new Date(email.sent_at).toLocaleString("id-ID")}</span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {email.attachment_filename && (
                  <span className="text-ink-600 inline-flex items-center gap-1 text-xs">
                    <Paperclip className="size-3" strokeWidth={1.75} />
                    {email.attachment_filename}
                  </span>
                )}
                {email.has_reply ? (
                  <span
                    className="text-success-700 inline-flex items-center gap-1 text-xs"
                    title={email.reply_snippet ?? undefined}
                  >
                    <CheckCircle2 className="size-3.5" strokeWidth={1.75} />
                    Dibalas kandidat
                  </span>
                ) : (
                  <span className="caption">Belum dibalas</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
