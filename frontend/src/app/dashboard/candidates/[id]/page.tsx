"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/require-auth";
import { TagInput } from "@/components/tag-input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { getCandidate, updateCandidate } from "@/lib/candidates/api";
import type { Candidate, CandidateStatus } from "@/lib/candidates/types";

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

const POLL_INTERVAL_MS = 2500;
const POLL_TIMEOUT_MS = 35000;

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
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const pollStart = useRef<number>(Date.now());

  const isProcessing = candidate?.status === "new" && candidate.parsed_profile === null;

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function load() {
      try {
        const data = await getCandidate(params.id);
        if (cancelled) return;
        setCandidate(data);

        const stillProcessing = data.status === "new" && data.parsed_profile === null;
        const elapsed = Date.now() - pollStart.current;
        if (stillProcessing && elapsed < POLL_TIMEOUT_MS) {
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
    <div className="max-w-2xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1>{candidate.full_name}</h1>
          <p className="text-ink-600 text-sm">
            {candidate.email} • {candidate.phone}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isProcessing ? (
            <Badge className="bg-secondary text-primary animate-pulse">Memproses...</Badge>
          ) : (
            <Badge className={STATUS_BADGE[candidate.status]}>{STATUS_LABEL[candidate.status]}</Badge>
          )}
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

      {isProcessing && (
        <p className="text-ink-400 text-sm">Sedang mem-parsing CV... halaman ini akan update otomatis.</p>
      )}

      {!isProcessing && profile && (
        <ParsedProfileSection candidate={candidate} profile={profile} editing={editing} setEditing={setEditing} onSaved={setCandidate} />
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
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const updatedProfile = {
        ...profile,
        skills: { value: skills, verified: true },
        education: { value: education.split("\n").filter(Boolean), verified: true },
        experience: { value: experience.split("\n").filter(Boolean), verified: true },
      };
      const updated = await updateCandidate(candidate.id, { parsed_profile: updatedProfile });
      onSaved(updated);
      setEditing(false);
      toast.success("Koreksi disimpan");
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
