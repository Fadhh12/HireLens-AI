"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { TagInput } from "@/components/tag-input";
import { ApiError } from "@/lib/api/client";
import { closeJob, createJob, updateJob } from "@/lib/jobs/api";
import type { JobLevel, JobPosting, JobPostingInput } from "@/lib/jobs/types";

const LEVEL_LABEL: Record<JobLevel, string> = {
  junior: "Junior",
  mid: "Mid",
  senior: "Senior",
};

interface JobFormProps {
  initialJob?: JobPosting;
}

export function JobForm({ initialJob }: JobFormProps) {
  const router = useRouter();
  const isEdit = Boolean(initialJob);
  const isClosed = initialJob?.status === "closed";

  const [title, setTitle] = useState(initialJob?.title ?? "");
  const [department, setDepartment] = useState(initialJob?.department ?? "");
  const [description, setDescription] = useState(initialJob?.description ?? "");
  const [requiredSkills, setRequiredSkills] = useState<string[]>(initialJob?.required_skills ?? []);
  const [niceToHaveSkills, setNiceToHaveSkills] = useState<string[]>(
    initialJob?.nice_to_have_skills ?? []
  );
  const [minExperience, setMinExperience] = useState(initialJob?.min_experience_years ?? 0);
  const [level, setLevel] = useState<JobLevel>(initialJob?.level ?? "mid");
  const [weightSkill, setWeightSkill] = useState(initialJob?.weight_skill_fit ?? 50);
  const [weightExperience, setWeightExperience] = useState(initialJob?.weight_experience_fit ?? 30);
  const [weightValues, setWeightValues] = useState(initialJob?.weight_values_fit ?? 20);
  const [submitting, setSubmitting] = useState<"draft" | "publish" | "close" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const weightTotal = weightSkill + weightExperience + weightValues;
  const weightValid = Math.abs(weightTotal - 100) < 0.01;
  const canPublish = requiredSkills.length > 0;

  function buildPayload(status: "draft" | "active"): JobPostingInput {
    return {
      title,
      department,
      description,
      required_skills: requiredSkills,
      nice_to_have_skills: niceToHaveSkills,
      min_experience_years: minExperience,
      level,
      weight_skill_fit: weightSkill,
      weight_experience_fit: weightExperience,
      weight_values_fit: weightValues,
      status,
    };
  }

  async function handleSave(status: "draft" | "active") {
    setError(null);
    setSubmitting(status === "draft" ? "draft" : "publish");
    try {
      const payload = buildPayload(status);
      const job =
        isEdit && initialJob
          ? await updateJob(initialJob.id, payload)
          : await createJob(payload);
      toast.success(status === "active" ? "Job dipublish" : "Job disimpan sebagai draft");
      router.push(`/dashboard/jobs/${job.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : "Gagal menyimpan job posting");
    } finally {
      setSubmitting(null);
    }
  }

  async function handleClose() {
    if (!initialJob) return;
    setSubmitting("close");
    try {
      await closeJob(initialJob.id);
      toast.success("Lowongan ditutup");
      router.push("/dashboard/jobs");
      router.refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal menutup lowongan");
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      {isClosed && (
        <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">
          Job posting ini sudah <strong>closed</strong> — kriteria & data tidak bisa diedit lagi
          (BR-2), untuk menjaga histori skor kandidat tetap konsisten.
        </p>
      )}

      {/* 1. Info dasar */}
      <section className="space-y-3">
        <h2>Info Dasar</h2>
        <div className="space-y-1.5">
          <Label htmlFor="job-title">Judul posisi</Label>
          <Input
            id="job-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isClosed}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="job-department">Department</Label>
          <Input
            id="job-department"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            disabled={isClosed}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="job-description">Deskripsi</Label>
          <Textarea
            id="job-description"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isClosed}
          />
        </div>
      </section>

      {/* 2 & 3. Skills */}
      <section className="space-y-3">
        <h2>Skill</h2>
        <div className="space-y-1.5">
          <Label htmlFor="required-skills">Skill wajib</Label>
          <TagInput
            id="required-skills"
            value={requiredSkills}
            onChange={setRequiredSkills}
            placeholder="Ketik skill lalu Enter"
          />
          <p className="caption">Minimal 1 skill wajib sebelum job bisa di-publish (FR-2.2).</p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="nice-to-have-skills">Skill nice-to-have</Label>
          <TagInput
            id="nice-to-have-skills"
            value={niceToHaveSkills}
            onChange={setNiceToHaveSkills}
            placeholder="Ketik skill lalu Enter"
          />
        </div>
      </section>

      {/* 4. Pengalaman & level */}
      <section className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="min-experience">Pengalaman minimum (tahun)</Label>
          <Input
            id="min-experience"
            type="number"
            min={0}
            value={minExperience}
            onChange={(e) => setMinExperience(Number(e.target.value))}
            disabled={isClosed}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="level">Level</Label>
          <Select value={level} onValueChange={(v) => setLevel(v as JobLevel)}>
            <SelectTrigger id="level" className="w-full" disabled={isClosed}>
              <SelectValue>{LEVEL_LABEL[level]}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(LEVEL_LABEL) as JobLevel[]).map((l) => (
                <SelectItem key={l} value={l}>
                  {LEVEL_LABEL[l]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </section>

      {/* 5. Bobot scoring */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2>Bobot Scoring</h2>
          <span
            className={`tabular-score text-sm ${weightValid ? "text-success-700" : "text-danger-700"}`}
          >
            Total {weightTotal.toFixed(0)}%{!weightValid && " — harus 100%"}
          </span>
        </div>

        <WeightSlider label="Skill Fit" value={weightSkill} onChange={setWeightSkill} disabled={isClosed} />
        <WeightSlider
          label="Experience Fit"
          value={weightExperience}
          onChange={setWeightExperience}
          disabled={isClosed}
        />
        <WeightSlider
          label="Values Fit"
          value={weightValues}
          onChange={setWeightValues}
          disabled={isClosed}
        />
      </section>

      {error && <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">{error}</p>}

      {!isClosed && (
        <div className="flex items-center gap-3 pt-2">
          <Button
            variant="secondary"
            disabled={!weightValid || submitting !== null}
            onClick={() => handleSave("draft")}
          >
            {submitting === "draft" ? "Menyimpan..." : "Simpan sebagai Draft"}
          </Button>
          <Button
            disabled={!weightValid || !canPublish || submitting !== null}
            onClick={() => handleSave("active")}
            title={!canPublish ? "Tambahkan minimal 1 skill wajib dulu" : undefined}
          >
            {submitting === "publish" ? "Mempublish..." : "Publish"}
          </Button>
          {isEdit && initialJob?.status === "active" && (
            <Button
              variant="outline"
              disabled={submitting !== null}
              onClick={handleClose}
              className="ml-auto"
            >
              {submitting === "close" ? "Menutup..." : "Tutup Lowongan"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

function WeightSlider({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="tabular-score">{value}%</span>
      </div>
      <Slider
        value={[value]}
        onValueChange={(v) => onChange(Array.isArray(v) ? v[0] : v)}
        min={0}
        max={100}
        step={1}
        disabled={disabled}
      />
    </div>
  );
}
