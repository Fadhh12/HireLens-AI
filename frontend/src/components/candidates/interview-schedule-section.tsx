"use client";

import { ExternalLink, Video } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";
import {
  disconnectGoogle,
  getGoogleConnectUrl,
  getGoogleConnectionStatus,
  listInterviewSchedules,
  scheduleInterview,
} from "@/lib/scheduling/api";
import type { GoogleConnectionStatus, InterviewSchedule } from "@/lib/scheduling/types";

const DURATION_OPTIONS = [15, 30, 45, 60];

/** FR-8-adjacent, not in the original SDD (see backend
 * scheduling/model.py) — lets a recruiter/hiring manager schedule a real
 * interview with a Google Meet link once a candidate is shortlisted,
 * instead of only generating the AI question guide. Candidate gets
 * Google Calendar's own invite email automatically. */
export function InterviewScheduleSection({ candidateId }: { candidateId: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [connection, setConnection] = useState<GoogleConnectionStatus | null>(null);
  const [schedules, setSchedules] = useState<InterviewSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [duration, setDuration] = useState(30);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    Promise.all([getGoogleConnectionStatus(), listInterviewSchedules(candidateId)])
      .then(([conn, list]) => {
        setConnection(conn);
        setSchedules(list);
      })
      .catch(() => {
        // Best-effort — the rest of the candidate page still works without this section.
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateId]);

  useEffect(() => {
    const connected = searchParams.get("google_connected");
    const error = searchParams.get("google_error");
    if (!connected && !error) return;

    if (connected) toast.success("Google Calendar berhasil dihubungkan");
    if (error) toast.error(`Gagal menghubungkan Google Calendar: ${error}`);

    // Strip the query params so a refresh doesn't re-show the toast.
    router.replace(pathname);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  async function handleConnect() {
    setConnecting(true);
    try {
      const { authorize_url } = await getGoogleConnectUrl(pathname);
      window.location.href = authorize_url;
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memulai koneksi Google");
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true);
    try {
      await disconnectGoogle();
      setConnection({ connected: false, google_email: null });
      toast.success("Google Calendar diputuskan");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memutuskan koneksi");
    } finally {
      setDisconnecting(false);
    }
  }

  async function handleSchedule() {
    if (!scheduledAt) {
      toast.error("Pilih tanggal & waktu interview dulu");
      return;
    }
    setSubmitting(true);
    try {
      // <input type="datetime-local"> is naive — new Date() attaches the
      // browser's own timezone offset, which is what the backend expects.
      const iso = new Date(scheduledAt).toISOString();
      const created = await scheduleInterview(candidateId, { scheduled_at: iso, duration_minutes: duration });
      setSchedules((prev) => [created, ...prev]);
      setScheduledAt("");
      toast.success("Interview dijadwalkan — undangan Google Meet terkirim ke email kandidat");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal menjadwalkan interview");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <section className="border-border bg-card space-y-3 rounded-lg border p-4">
        <h2>Jadwalkan Interview</h2>
        <p className="text-ink-400 text-sm">Memuat...</p>
      </section>
    );
  }

  return (
    <section className="border-border bg-card space-y-4 rounded-lg border p-4">
      <h2>Jadwalkan Interview</h2>

      {!connection?.connected ? (
        <div className="space-y-2">
          <p className="text-ink-600 text-sm">
            Hubungkan Google Calendar Anda untuk membuat link Google Meet dan mengundang kandidat otomatis.
          </p>
          <Button onClick={handleConnect} disabled={connecting}>
            {connecting ? "Membuka Google..." : "Hubungkan Google Calendar"}
          </Button>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="text-ink-600">
              Terhubung sebagai <span className="font-medium">{connection.google_email}</span>
            </span>
            <Button variant="ghost" size="sm" onClick={handleDisconnect} disabled={disconnecting}>
              {disconnecting ? "Memutuskan..." : "Putuskan koneksi"}
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto_auto]">
            <div className="space-y-1.5">
              <Label htmlFor="interview-datetime">Tanggal & waktu</Label>
              <input
                id="interview-datetime"
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="border-input h-8 w-full rounded-lg border bg-transparent px-2.5 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Durasi</Label>
              <Select value={String(duration)} onValueChange={(v) => setDuration(Number(v))}>
                <SelectTrigger className="w-28">
                  <SelectValue>{duration} menit</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {DURATION_OPTIONS.map((d) => (
                    <SelectItem key={d} value={String(d)}>
                      {d} menit
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={handleSchedule} disabled={submitting} className="w-full sm:w-auto">
                {submitting ? "Menjadwalkan..." : "Jadwalkan"}
              </Button>
            </div>
          </div>
        </>
      )}

      {schedules.length > 0 && (
        <ul className="divide-border divide-y">
          {schedules.map((s) => (
            <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <div className="flex items-center gap-2">
                <Video className="text-primary size-4 shrink-0" strokeWidth={1.75} />
                <span>
                  {new Date(s.scheduled_at).toLocaleString("id-ID", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </span>
                <span className="caption">({s.duration_minutes} menit)</span>
              </div>
              <a
                href={s.meet_link}
                target="_blank"
                rel="noreferrer"
                className="text-primary inline-flex items-center gap-1 hover:underline"
              >
                Google Meet
                <ExternalLink className="size-3.5" strokeWidth={1.75} />
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
