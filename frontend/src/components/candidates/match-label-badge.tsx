import { Badge } from "@/components/ui/badge";
import type { MatchLabel } from "@/lib/candidates/types";

export const MATCH_LABEL_TEXT: Record<MatchLabel, string> = {
  strong_match: "Strong Match",
  consider: "Consider",
  not_a_fit: "Not a Fit",
};

const MATCH_LABEL_CLASS: Record<MatchLabel, string> = {
  strong_match: "bg-success-100 text-success-700",
  consider: "bg-warning-100 text-warning-700",
  not_a_fit: "bg-danger-100 text-danger-700",
};

/** UI/UX §2.4 Score Badge — color + text together, never color alone. */
export function MatchLabelBadge({ label }: { label: MatchLabel }) {
  return <Badge className={MATCH_LABEL_CLASS[label]}>{MATCH_LABEL_TEXT[label]}</Badge>;
}
