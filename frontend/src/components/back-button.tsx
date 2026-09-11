"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

interface BackButtonProps {
  /** Where to land when there's no in-app history to pop (deep link, page
   * refresh, opened in a new tab) — router.back() would otherwise leave the
   * app or land on a blank entry. */
  fallbackHref: string;
  label?: string;
  className?: string;
}

/** Consistent "Kembali" affordance for detail/nested pages so users aren't
 * forced back to the sidebar nav to go up one level. */
export function BackButton({ fallbackHref, label = "Kembali", className }: BackButtonProps) {
  const router = useRouter();

  function handleClick() {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
    } else {
      router.push(fallbackHref);
    }
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={handleClick}
      className={`text-ink-600 -ml-2.5 gap-1.5 ${className ?? ""}`}
    >
      <ArrowLeft className="size-4" strokeWidth={1.75} />
      {label}
    </Button>
  );
}
