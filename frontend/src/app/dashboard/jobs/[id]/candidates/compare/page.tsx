"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import { MatchLabelBadge } from "@/components/candidates/match-label-badge";
import { getCandidate } from "@/lib/candidates/api";
import type { Candidate } from "@/lib/candidates/types";
import { getCandidateScore } from "@/lib/matching/api";
import type { CandidateScore } from "@/lib/matching/types";

interface Row {
  candidate: Candidate;
  score: CandidateScore | null;
}

export default function CandidateComparePage() {
  return (
    <RequireAuth allowedRoles={["admin", "recruiter", "hiring_manager"]}>
      <CandidateCompareContent />
    </RequireAuth>
  );
}

function CandidateCompareContent() {
  useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const ids = (searchParams.get("ids") ?? "").split(",").filter(Boolean);
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all(
      ids.map(async (id) => {
        const candidate = await getCandidate(id);
        const score = await getCandidateScore(id).catch(() => null);
        return { candidate, score };
      })
    )
      .then(setRows)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  if (loading) return <p className="text-ink-400 text-sm">Memuat...</p>;
  if (rows.length < 2) {
    return <p className="text-danger-700 text-sm">Pilih minimal 2 kandidat dari Ranking Dashboard untuk dibandingkan.</p>;
  }

  const allSkills = Array.from(
    new Set(rows.flatMap((r) => (r.candidate.parsed_profile?.skills?.value ?? [])))
  );

  return (
    <div className="space-y-4">
      <h1>Bandingkan Kandidat</h1>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="text-ink-400 border-border w-40 border-b p-2 text-left font-normal">—</th>
              {rows.map((r) => (
                <th key={r.candidate.id} className="border-border min-w-48 border-b p-2 text-left">
                  {r.candidate.full_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <CompareRow label="Skor Akhir">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border tabular-score border-b p-2">
                  {r.score ? r.score.final_score.toFixed(1) : "—"}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Label">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border border-b p-2">
                  {r.score ? <MatchLabelBadge label={r.score.label} /> : "—"}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Skill Fit">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border border-b p-2">
                  {r.score?.score_breakdown.skill_fit.score ?? "—"}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Experience Fit">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border border-b p-2">
                  {r.score?.score_breakdown.experience_fit.score ?? "—"} (
                  {r.score?.score_breakdown.experience_fit.candidate_years ?? "?"} thn)
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Values Fit">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border border-b p-2">
                  {r.score?.score_breakdown.values_fit.score ?? "—"}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Status">
              {rows.map((r) => (
                <td key={r.candidate.id} className="border-border border-b p-2">
                  {r.candidate.status}
                </td>
              ))}
            </CompareRow>
            {allSkills.map((skill) => (
              <CompareRow key={skill} label={skill}>
                {rows.map((r) => {
                  const has = (r.candidate.parsed_profile?.skills?.value ?? []).includes(skill);
                  return (
                    <td key={r.candidate.id} className="border-border border-b p-2">
                      <span className={has ? "text-success-700" : "text-ink-400"}>{has ? "✓" : "—"}</span>
                    </td>
                  );
                })}
              </CompareRow>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CompareRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <tr>
      <td className="border-border text-ink-600 border-b p-2 font-medium">{label}</td>
      {children}
    </tr>
  );
}
