import { Aperture } from "lucide-react";

/** Brand mark — an aperture (the "lens" in HireLens: focusing in on the
 * right candidate). Deep teal badge per the design system's brand color,
 * a thin amber ring as the one deliberately sparing accent touch (§2.1:
 * amber is reserved for small, premium-feeling highlights, never a
 * dominant color) — no gradient, no glow, per §1's "trust over trend". */
export function Logomark({ size = "md" }: { size?: "sm" | "md" }) {
  const box = size === "sm" ? "size-7" : "size-8";
  const icon = size === "sm" ? "size-4" : "size-4.5";
  return (
    <span
      className={`${box} bg-primary text-primary-foreground ring-amber-600/50 inline-flex shrink-0 items-center justify-center rounded-lg ring-1`}
    >
      <Aperture className={icon} strokeWidth={2} />
    </span>
  );
}
