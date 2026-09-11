interface DonutChartSegment {
  label: string;
  value: number;
  /** CSS custom property name, e.g. "--success-700" — resolved via var(). */
  colorVar: string;
}

interface DonutChartProps {
  segments: DonutChartSegment[];
  size?: number;
  strokeWidth?: number;
  centerValue?: string;
  centerLabel?: string;
}

/** Dependency-free SVG donut — matches the app's existing hand-rolled bar
 * charts (ScoreBreakdownBar, dashboard label-distribution bars) instead of
 * pulling in a charting library for one visual. */
export function DonutChart({
  segments,
  size = 168,
  strokeWidth = 22,
  centerValue,
  centerLabel,
}: DonutChartProps) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  let cumulative = 0;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--muted)"
          strokeWidth={strokeWidth}
        />
        {total > 0 &&
          segments.map((s) => {
            if (s.value <= 0) return null;
            const fraction = s.value / total;
            const dash = fraction * circumference;
            const offset = cumulative * circumference;
            cumulative += fraction;
            return (
              <circle
                key={s.label}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={`var(${s.colorVar})`}
                strokeWidth={strokeWidth}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
              >
                <title>{s.label}</title>
              </circle>
            );
          })}
      </svg>
      {(centerValue || centerLabel) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {centerValue && <p className="tabular-score text-2xl">{centerValue}</p>}
          {centerLabel && <p className="caption text-center leading-tight">{centerLabel}</p>}
        </div>
      )}
    </div>
  );
}
