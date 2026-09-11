import type { MatchLabel } from "@/lib/candidates/types";

// Same match-label palette as MatchLabelBadge — success/warning/danger are
// reserved for Strong Match/Consider/Not a Fit only (design system §2.1).
const RING_COLOR_VAR: Record<MatchLabel, string> = {
  strong_match: "--success-700",
  consider: "--warning-700",
  not_a_fit: "--danger-700",
};

interface ScoreRingProps {
  score: number;
  label: MatchLabel | null;
  size?: number;
  strokeWidth?: number;
}

/** Small circular score indicator for candidate rows/cards — turns the
 * label color into a visual proportion instead of flat text/badge alone. */
export function ScoreRing({ score, label, size = 40, strokeWidth = 4 }: ScoreRingProps) {
  const colorVar = label ? RING_COLOR_VAR[label] : "--ink-400";
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, score));
  const dash = (pct / 100) * circumference;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} title={`${pct.toFixed(1)}%`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--muted)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`var(${colorVar})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="tabular-score text-[0.65rem]">{pct.toFixed(0)}</span>
      </div>
    </div>
  );
}
