"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/require-auth";
import { FileDropzone } from "@/components/file-dropzone";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { intakeCandidate } from "@/lib/candidates/api";

const COMPETENCY_CATEGORIES = [
  { key: "communication", label: "Komunikasi" },
  { key: "leadership", label: "Kepemimpinan" },
  { key: "problem_solving", label: "Problem Solving" },
  { key: "teamwork", label: "Kerja Tim" },
] as const;

export default function CandidateIntakePage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter"]}>
      <CandidateIntakeContent />
    </RequireAuth>
  );
}

function CandidateIntakeContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [cvFiles, setCvFiles] = useState<File[]>([]);
  const [certFiles, setCertFiles] = useState<File[]>([]);
  const [mbti, setMbti] = useState("");
  const [scores, setScores] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (cvFiles.length === 0) {
      setError("File CV wajib diunggah");
      return;
    }

    setSubmitting(true);
    try {
      const hasAssessment = mbti.trim() !== "" || Object.keys(scores).length > 0;
      const result = await intakeCandidate(params.id, {
        full_name: fullName,
        email,
        phone,
        cv_file: cvFiles[0],
        certificate_files: certFiles,
        assessment_input: hasAssessment
          ? { mbti: mbti.trim() || null, competency_scores: scores }
          : undefined,
      });

      if (result.duplicate_warning) {
        toast.warning("Email ini sudah pernah apply ke job ini sebelumnya — tetap disimpan sebagai entri baru.");
      }
      toast.success("Kandidat diunggah, sedang diproses...");
      router.push(`/dashboard/candidates/${result.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : "Gagal mengunggah kandidat");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h1>Tambah Kandidat</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <FileDropzone
          label="CV Kandidat *"
          accept=".pdf,.docx"
          hint="PDF atau DOCX, maks 5MB"
          files={cvFiles}
          onChange={setCvFiles}
        />

        <FileDropzone
          label="Sertifikat (opsional)"
          accept=".pdf,.jpg,.jpeg,.png"
          hint="PDF/JPG/PNG, maks 5 file, masing-masing 5MB"
          multiple
          files={certFiles}
          onChange={setCertFiles}
        />

        <section className="space-y-3">
          <h2>Data Diri</h2>
          <div className="space-y-1.5">
            <Label htmlFor="full-name">Nama lengkap</Label>
            <Input id="full-name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cand-email">Email</Label>
            <Input
              id="cand-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cand-phone">Nomor telepon</Label>
            <Input
              id="cand-phone"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="0812-3456-7890"
            />
          </div>
        </section>

        <section className="space-y-3">
          <h2>Hasil Asesmen (opsional)</h2>
          <p className="caption">
            Tidak ada integrasi psikotes eksternal di MVP — isi manual jika hasilnya sudah ada.
          </p>
          <div className="space-y-1.5">
            <Label htmlFor="mbti">Tipe MBTI</Label>
            <Input id="mbti" value={mbti} onChange={(e) => setMbti(e.target.value)} placeholder="cth. INTJ" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {COMPETENCY_CATEGORIES.map((c) => (
              <div key={c.key} className="space-y-1.5">
                <Label htmlFor={`score-${c.key}`}>{c.label} (1-5)</Label>
                <Input
                  id={`score-${c.key}`}
                  type="number"
                  min={1}
                  max={5}
                  value={scores[c.key] ?? ""}
                  onChange={(e) =>
                    setScores((prev) => ({ ...prev, [c.key]: Number(e.target.value) }))
                  }
                />
              </div>
            ))}
          </div>
        </section>

        {error && <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">{error}</p>}

        <Button type="submit" disabled={submitting}>
          {submitting ? "Mengunggah..." : "Unggah & Proses Kandidat"}
        </Button>
      </form>
    </div>
  );
}
