"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/require-auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";
import {
  finalizeGuide,
  listGuideVersions,
  triggerGenerateGuide,
  updateGuide,
} from "@/lib/interview/api";
import type { InterviewGuide } from "@/lib/interview/types";

const POLL_INTERVAL_MS = 2500;
const POLL_TIMEOUT_MS = 30000;

export default function InterviewGuidePage() {
  return (
    <RequireAuth allowedRoles={["admin", "interviewer"]}>
      <InterviewGuideContent />
    </RequireAuth>
  );
}

function InterviewGuideContent() {
  const params = useParams<{ id: string }>();
  const [versions, setVersions] = useState<InterviewGuide[]>([]);
  const [selected, setSelected] = useState<InterviewGuide | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const generateStart = useRef(0);

  const [technical, setTechnical] = useState<string[]>([]);
  const [behavioral, setBehavioral] = useState<string[]>([]);
  const [riskAreas, setRiskAreas] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  async function loadAll(preferLatest = false) {
    try {
      const list = await listGuideVersions(params.id);
      setVersions(list);
      if (list.length > 0) {
        const target = preferLatest ? list[0] : selected ? list.find((g) => g.id === selected.id) ?? list[0] : list[0];
        setSelected(target);
        setTechnical(target.technical_questions);
        setBehavioral(target.behavioral_questions);
        setRiskAreas(target.risk_areas);
      }
    } catch {
      // no guide yet — fine, shows the empty state
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function handleGenerate() {
    setGenerating(true);
    generateStart.current = Date.now();
    try {
      await triggerGenerateGuide(params.id);
      poll();
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memulai generate");
      setGenerating(false);
    }
  }

  async function poll() {
    const previousCount = versions.length;
    const check = async () => {
      const list = await listGuideVersions(params.id).catch(() => []);
      if (list.length > previousCount) {
        setVersions(list);
        setSelected(list[0]);
        setTechnical(list[0].technical_questions);
        setBehavioral(list[0].behavioral_questions);
        setRiskAreas(list[0].risk_areas);
        setGenerating(false);
        toast.success("Pertanyaan interview berhasil dibuat");
        return;
      }
      if (Date.now() - generateStart.current < POLL_TIMEOUT_MS) {
        setTimeout(check, POLL_INTERVAL_MS);
      } else {
        setGenerating(false);
        toast.error("Generate memakan waktu terlalu lama — coba lagi");
      }
    };
    setTimeout(check, POLL_INTERVAL_MS);
  }

  function selectVersion(id: string | null) {
    const g = versions.find((v) => v.id === id);
    if (!g) return;
    setSelected(g);
    setTechnical(g.technical_questions);
    setBehavioral(g.behavioral_questions);
    setRiskAreas(g.risk_areas);
  }

  async function handleSave() {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await updateGuide(selected.id, {
        technical_questions: technical,
        behavioral_questions: behavioral,
        risk_areas: riskAreas,
      });
      setSelected(updated);
      setVersions((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
      toast.success("Perubahan disimpan");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal menyimpan");
    } finally {
      setSaving(false);
    }
  }

  async function handleFinalize() {
    if (!selected) return;
    try {
      const updated = await finalizeGuide(selected.id);
      setSelected(updated);
      setVersions((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
      toast.success("Interview guide difinalisasi");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal finalisasi");
    }
  }

  if (loading) return <p className="text-ink-400 text-sm">Memuat...</p>;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1>Interview Guide</h1>
        <div className="flex flex-wrap items-center gap-2">
          {versions.length > 0 && (
            <Select value={selected?.id} onValueChange={selectVersion}>
              <SelectTrigger className="w-28">
                <SelectValue>v{selected?.version}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {versions.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    v{v.version} {v.is_final ? "(final)" : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? "Menyusun..." : versions.length > 0 ? "Generate Ulang" : "Generate Pertanyaan"}
          </Button>
        </div>
      </div>

      {generating && (
        <p className="text-ink-400 text-sm">Menyusun pertanyaan berdasarkan profil kandidat...</p>
      )}

      {!generating && versions.length === 0 && (
        <p className="text-ink-400 text-sm">
          Belum ada interview guide. Klik &quot;Generate Pertanyaan&quot; untuk membuatnya.
        </p>
      )}

      {selected && !generating && (
        <div className="space-y-6">
          {selected.is_final && <Badge className="bg-success-100 text-success-700">Final</Badge>}

          <QuestionList
            label="Pertanyaan Teknikal"
            items={technical}
            onChange={setTechnical}
            readOnly={selected.is_final}
          />
          <QuestionList
            label="Pertanyaan Behavioral"
            items={behavioral}
            onChange={setBehavioral}
            readOnly={selected.is_final}
          />
          <QuestionList
            label="Area yang Perlu Digali"
            items={riskAreas}
            onChange={setRiskAreas}
            readOnly={selected.is_final}
          />

          {!selected.is_final && (
            <div className="flex items-center gap-3">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "Menyimpan..." : "Simpan Perubahan"}
              </Button>
              <Button variant="outline" onClick={handleFinalize}>
                Finalisasi Guide
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function QuestionList({
  label,
  items,
  onChange,
  readOnly,
}: {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  readOnly?: boolean;
}) {
  const [draft, setDraft] = useState("");

  return (
    <section className="space-y-2">
      <h2>{label}</h2>
      <ul className="space-y-2">
        {items.map((q, i) => (
          <li key={i} className="flex items-start gap-2">
            {readOnly ? (
              <p className="text-sm">
                {i + 1}. {q}
              </p>
            ) : (
              <>
                <Input
                  value={q}
                  onChange={(e) => {
                    const next = [...items];
                    next[i] = e.target.value;
                    onChange(next);
                  }}
                  className="flex-1"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onChange(items.filter((_, idx) => idx !== i))}
                >
                  Hapus
                </Button>
              </>
            )}
          </li>
        ))}
      </ul>
      {!readOnly && (
        <div className="flex items-center gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Tambah pertanyaan manual..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && draft.trim()) {
                e.preventDefault();
                onChange([...items, draft.trim()]);
                setDraft("");
              }
            }}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (draft.trim()) {
                onChange([...items, draft.trim()]);
                setDraft("");
              }
            }}
          >
            Tambah
          </Button>
        </div>
      )}
    </section>
  );
}
