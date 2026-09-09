import type { ScoreBreakdown } from "@/lib/matching/types";

interface Segment {
  label: string;
  score: number | null;
  weight: number;
  opacity: number;
}

/** UI/UX §2.4: horizontal stacked bar, 3 segments sized by each
 * component's weight, shaded (not multi-colored) so it reads as one
 * system rather than a rainbow. */
export function ScoreBreakdownBar({ breakdown }: { breakdown: ScoreBreakdown }) {
  const segments: Segment[] = [
    { label: "Skill Fit", score: breakdown.skill_fit.score, weight: breakdown.skill_fit.weight, opacity: 1 },
    {
      label: "Experience Fit",
      score: breakdown.experience_fit.score,
      weight: breakdown.experience_fit.weight,
      opacity: 0.65,
    },
    { label: "Values Fit", score: breakdown.values_fit.score, weight: breakdown.values_fit.weight, opacity: 0.35 },
  ];
  const totalWeight = segments.reduce((sum, s) => sum + s.weight, 0) || 1;

  return (
    <div className="space-y-2">
      <div className="border-border flex h-3 overflow-hidden rounded-full border">
        {segments.map((s) =>
          s.weight > 0 ? (
            <div
              key={s.label}
              style={{ width: `${(s.weight / totalWeight) * 100}%`, backgroundColor: `color-mix(in oklab, var(--primary) ${s.opacity * 100}%, transparent)` }}
              title={`${s.label}: ${s.score ?? "-"} (bobot ${s.weight}%)`}
            />
          ) : null
        )}
      </div>
      <div className="grid grid-cols-3 gap-2">
        {segments.map((s) => (
          <div key={s.label} className="space-y-0.5">
            <div className="flex items-center gap-1.5">
              <span
                className="size-2 shrink-0 rounded-full"
                style={{ backgroundColor: `color-mix(in oklab, var(--primary) ${s.opacity * 100}%, transparent)` }}
              />
              <span className="caption">{s.label}</span>
            </div>
            <p className="tabular-score text-sm">
              {s.score !== null ? s.score.toFixed(1) : "—"}{" "}
              <span className="caption">({s.weight.toFixed(0)}%)</span>
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
