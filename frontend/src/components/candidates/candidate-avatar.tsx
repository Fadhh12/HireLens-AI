import { initials } from "@/lib/initials";

const SIZE_CLASS = {
  sm: "size-8 text-xs",
  md: "size-10 text-sm",
  lg: "size-16 text-lg",
} as const;

interface CandidateAvatarProps {
  name: string;
  photoUrl?: string | null;
  size?: keyof typeof SIZE_CLASS;
  className?: string;
}

/** Photo when the candidate has one (uploaded at intake), initials circle
 * otherwise — same fallback pattern as the header's user avatar. */
export function CandidateAvatar({ name, photoUrl, size = "md", className }: CandidateAvatarProps) {
  const sizeClass = SIZE_CLASS[size];

  if (photoUrl) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- signed Supabase URLs, not a domain we can whitelist for next/image
      <img
        src={photoUrl}
        alt={name}
        className={`${sizeClass} shrink-0 rounded-full object-cover ${className ?? ""}`}
      />
    );
  }

  return (
    <span
      className={`bg-secondary text-primary flex shrink-0 items-center justify-center rounded-full font-medium ${sizeClass} ${className ?? ""}`}
    >
      {initials(name)}
    </span>
  );
}
