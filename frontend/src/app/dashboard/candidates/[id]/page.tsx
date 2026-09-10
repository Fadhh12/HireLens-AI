"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import Link from "next/link";

import { RequireAuth } from "@/components/require-auth";
import { MatchLabelBadge } from "@/components/candidates/match-label-badge";
import { ScoreBreakdownBar } from "@/components/candidates/score-breakdown-bar";
import { TagInput } from "@/components/tag-input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import {
  downloadCandidateReportPdf,
  getCandidate,
  updateCandidate,
  updateCandidateStatus,
} from "@/lib/candidates/api";
import type { Candidate, CandidateStatus } from "@/lib/candidates/types";
import { getCandidateScore } from "@/lib/matching/api";
import type { CandidateScore } from "@/lib/matching/types";

// UI/UX Layar 7: Interview Guide tab appears once shortlisted+.
const INTERVIEW_GUIDE_ELIGIBLE: CandidateStatus[] = ["shortlisted", "interviewed", "hired", "rejected"];

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
// (Strong Match/Consider/Not a Fit) ONLY — see the same badge on the score
// panel of this page — so pipeline status reads off the ink/primary scale
// instead (Task 6.3 finding).
const STATUS_BADGE: Record<CandidateStatus, string> = {
  new: "bg-muted text-ink-600",
  screening: "bg-secondary text-primary",
  shortlisted: "bg-secondary text-primary",
  interviewed: "bg-primary text-primary-foreground",
  hired: "bg-primary text-primary-foreground",
  rejected: "bg-ink-900/10 text-ink-900",
  needs_manual_review: "border border-ink-400 text-ink-900",
};

// FR-7.2: recruiter/hiring manager can move a candidate through this flow.
const STATUS_OPTIONS: CandidateStatus[] = [
  "new",
  "screening",
  "shortlisted",
  "interviewed",
  "hired",
  "rejected",
];

const POLL_INTERVAL_MS = 2500;
const POLL_TIMEOUT_MS = 40000;

export default function CandidateDetailPage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <CandidateDetailContent />
    </RequireAuth>
  );
}

function VerifiedTag({ verified }: { verified: boolean }) {
  return (
    <span className={`caption rounded px-1.5 py-0.5 ${verified ? "bg-success-100 text-success-700" : "bg-warning-100 text-warning-700"}`}>
      {verified ? "Terverifikasi" : "Perlu dicek"}
    </span>
  );
}

function CandidateDetailContent() {
  const params = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [score, setScore] = useState<CandidateScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const pollStart = useRef<number>(Date.now());

  const isParsing = candidate?.status === "new" && candidate.parsed_profile === null;
  const isScoring = candidate !== null && !isParsing && score === null;

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function load() {
      try {
        const data = await getCandidate(params.id);
        if (cancelled) return;
        setCandidate(data);

        const parsingDone = !(data.status === "new" && data.parsed_profile === null);
        let scoreData: CandidateScore | null = null;
        if (parsingDone) {
          try {
            scoreData = await getCandidateScore(params.id);
            if (cancelled) return;
            setScore(scoreData);
          } catch {
            // 404 until the score task finishes — keep polling below.
          }
        }

        const elapsed = Date.now() - pollStart.current;
        const stillWaiting = !parsingDone || scoreData === null;
        if (stillWaiting && elapsed < POLL_TIMEOUT_MS) {
          timer = setTimeout(load, POLL_INTERVAL_MS);
        }
      } catch (err) {
        toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memuat kandidat");
      } finally {
        setLoading(false);
      }
    }
    load();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [params.id]);

  if (loading && !candidate) return <p className="text-ink-400 text-sm">Memuat...</p>;
  if (!candidate) return <p className="text-danger-700 text-sm">Kandidat tidak ditemukan.</p>;

  const profile = candidate.parsed_profile;

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1>{candidate.full_name}</h1>
          <p className="text-ink-600 text-sm">
            {candidate.email} • {candidate.phone}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isParsing || isScoring ? (
            <Badge className="bg-secondary text-primary animate-pulse">
              {isParsing ? "Memproses CV..." : "Menghitung skor..."}
            </Badge>
          ) : (
            <Badge className={STATUS_BADGE[candidate.status]}>{STATUS_LABEL[candidate.status]}</Badge>
          )}
          {INTERVIEW_GUIDE_ELIGIBLE.includes(candidate.status) && (
            <Button
              variant="outline"
              size="sm"
              render={<Link href={`/dashboard/candidates/${candidate.id}/interview`}>Interview Guide</Link>}
              nativeButton={false}
            />
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              downloadCandidateReportPdf(candidate.id, `laporan-${candidate.full_name}.pdf`).catch(() =>
                toast.error("Gagal mengekspor laporan PDF")
              )
            }
          >
            Export PDF
          </Button>
        </div>
      </div>

      {candidate.status === "needs_manual_review" && (
        <p className="text-warning-700 bg-warning-100 rounded-md px-3 py-2 text-sm">
          Parsing CV otomatis gagal untuk kandidat ini (FR-3.5) — isi data profil secara manual di bawah.
        </p>
      )}
      {profile?.warnings && profile.warnings.length > 0 && (
        <ul className="text-warning-700 bg-warning-100 list-disc space-y-1 rounded-md px-6 py-2 text-sm">
          {profile.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
      {isParsing && <p className="text-ink-400 text-sm">Sedang mem-parsing CV... halaman ini akan update otomatis.</p>}
      {isScoring && <p className="text-ink-400 text-sm">Menghitung skor kecocokan... halaman ini akan update otomatis.</p>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-6">
          {score?.score_breakdown.candidate_summary && (
            <section className="space-y-2">
              <div className="flex items-center gap-2">
                <h2>Ringkasan</h2>
                <Badge className="bg-secondary text-primary">✨ Dibantu AI</Badge>
              </div>
              <p className="text-sm leading-relaxed">{score.score_breakdown.candidate_summary}</p>
            </section>
          )}

          {!isParsing && profile && (
            <ParsedProfileSection
              candidate={candidate}
              profile={profile}
              editing={editing}
              setEditing={setEditing}
              onSaved={setCandidate}
            />
          )}

          {candidate.assessment_input && (
            <section className="space-y-2">
              <h2>Hasil Asesmen Manual</h2>
              <pre className="border-border bg-card overflow-x-auto rounded-md border p-3 text-xs">
                {JSON.stringify(candidate.assessment_input, null, 2)}
              </pre>
            </section>
          )}
        </div>

        <div className="space-y-6">
          {score && (
            <section className="border-border bg-card space-y-4 rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <h2>Skor Kecocokan</h2>
                <MatchLabelBadge label={score.label} />
              </div>
              <p className="tabular-score text-3xl">{score.final_score.toFixed(1)}</p>
              <ScoreBreakdownBar breakdown={score.score_breakdown} />

              <div className="space-y-2 text-sm">
                {score.score_breakdown.skill_fit.missing_required.length > 0 && (
                  <p className="text-ink-600">
                    Skill wajib belum terpenuhi:{" "}
                    <span className="text-danger-700">
                      {score.score_breakdown.skill_fit.missing_required.join(", ")}
                    </span>
                  </p>
                )}
                <p className="text-ink-600">
                  Pengalaman: {score.score_breakdown.experience_fit.candidate_years} tahun (min.{" "}
                  {score.score_breakdown.experience_fit.required_years} tahun)
                </p>
                {score.score_breakdown.values_fit.note && (
                  <p className="text-ink-600">{score.score_breakdown.values_fit.note}</p>
                )}
              </div>
              <p className="caption">Model: {score.model_version}</p>
            </section>
          )}

          <StatusChangeSection candidate={candidate} onChanged={setCandidate} />
        </div>
      </div>
    </div>
  );
}

function StatusChangeSection({
  candidate,
  onChanged,
}: {
  candidate: Candidate;
  onChanged: (c: Candidate) => void;
}) {
  const [status, setStatus] = useState<CandidateStatus>(candidate.status);
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit() {
    if (!reason.trim()) {
      toast.error("Alasan perubahan status wajib diisi (BR-1)");
      return;
    }
    setSaving(true);
    try {
      const updated = await updateCandidateStatus(candidate.id, status, reason.trim());
      onChanged(updated);
      setReason("");
      toast.success("Status kandidat diperbarui");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal mengubah status");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="border-border bg-card space-y-3 rounded-lg border p-4">
      <h2>Ubah Status</h2>
      <div className="space-y-1.5">
        <Label htmlFor="status-select">Status baru</Label>
        <Select value={status} onValueChange={(v) => setStatus(v as CandidateStatus)}>
          <SelectTrigger id="status-select" className="w-full">
            <SelectValue>{STATUS_LABEL[status]}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((s) => (
              <SelectItem key={s} value={s}>
                {STATUS_LABEL[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="status-reason">Alasan (wajib)</Label>
        <Textarea
          id="status-reason"
          rows={2}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="cth. Skill teknis sangat sesuai kebutuhan tim"
        />
      </div>
      <Button onClick={handleSubmit} disabled={saving} className="w-full">
        {saving ? "Menyimpan..." : "Simpan Status"}
      </Button>
    </section>
  );
}

function ParsedProfileSection({
  candidate,
  profile,
  editing,
  setEditing,
  onSaved,
}: {
  candidate: Candidate;
  profile: NonNullable<Candidate["parsed_profile"]>;
  editing: boolean;
  setEditing: (v: boolean) => void;
  onSaved: (c: Candidate) => void;
}) {
  const [skills, setSkills] = useState<string[]>(profile.skills?.value ?? []);
  const [education, setEducation] = useState((profile.education?.value ?? []).join("\n"));
  const [experience, setExperience] = useState((profile.experience?.value ?? []).join("\n"));
  const [experienceYears, setExperienceYears] = useState(profile.experience_years?.value ?? 0);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const updatedProfile = {
        ...profile,
        skills: { value: skills, verified: true },
        education: { value: education.split("\n").filter(Boolean), verified: true },
        experience: { value: experience.split("\n").filter(Boolean), verified: true },
        experience_years: { value: experienceYears, verified: true },
      };
      const updated = await updateCandidate(candidate.id, { parsed_profile: updatedProfile });
      onSaved(updated);
      setEditing(false);
      toast.success("Koreksi disimpan — skor akan dihitung ulang");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal menyimpan koreksi");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2>Hasil Ekstraksi CV</h2>
        <Button variant="outline" size="sm" onClick={() => setEditing(!editing)}>
          {editing ? "Batal" : "Koreksi Manual"}
        </Button>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Label>Skill</Label>
          {!editing && profile.skills && <VerifiedTag verified={profile.skills.verified} />}
        </div>
        {editing ? (
          <TagInput value={skills} onChange={setSkills} placeholder="Ketik skill lalu Enter" />
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {(profile.skills?.value ?? []).length === 0 && (
              <p className="caption">Tidak ada skill terdeteksi.</p>
            )}
            {(profile.skills?.value ?? []).map((s) => (
              <span key={s} className="bg-secondary text-secondary-foreground rounded-md px-2 py-1 text-xs">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Label>Total tahun pengalaman</Label>
          {!editing && profile.experience_years && <VerifiedTag verified={profile.experience_years.verified} />}
        </div>
        {editing ? (
          <input
            type="number"
            step={0.5}
            min={0}
            value={experienceYears}
            onChange={(e) => setExperienceYears(Number(e.target.value))}
            className="border-input h-8 w-32 rounded-lg border bg-transparent px-2.5 text-sm"
          />
        ) : (
          <p className="tabular-score text-sm">{profile.experience_years?.value ?? 0} tahun</p>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Label>Riwayat Pendidikan</Label>
          {!editing && profile.education && <VerifiedTag verified={profile.education.verified} />}
        </div>
        {editing ? (
          <Textarea rows={3} value={education} onChange={(e) => setEducation(e.target.value)} />
        ) : (
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {(profile.education?.value ?? []).length === 0 && (
              <p className="caption">Tidak terdeteksi otomatis.</p>
            )}
            {(profile.education?.value ?? []).map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Label>Riwayat Pengalaman</Label>
          {!editing && profile.experience && <VerifiedTag verified={profile.experience.verified} />}
        </div>
        {editing ? (
          <Textarea rows={4} value={experience} onChange={(e) => setExperience(e.target.value)} />
        ) : (
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {(profile.experience?.value ?? []).length === 0 && (
              <p className="caption">Tidak terdeteksi otomatis.</p>
            )}
            {(profile.experience?.value ?? []).map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
      </div>

      {profile.certifications && profile.certifications.value.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Label>Sertifikasi</Label>
            <VerifiedTag verified={profile.certifications.verified} />
          </div>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {profile.certifications.value.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {editing && (
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Menyimpan..." : "Simpan Koreksi"}
        </Button>
      )}
    </section>
  );
}
