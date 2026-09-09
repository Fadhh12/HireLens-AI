"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { logout as logoutApi } from "@/lib/auth/api";
import { useAuthStore } from "@/lib/auth/store";
import type { UserRole } from "@/lib/auth/types";

interface NavItem {
  label: string;
  href: string;
  roles?: UserRole[];
  available: boolean;
}

// Full IA per UI/UX Flow §3 (Screen Inventory) — only Overview and User
// Management are actually built in Phase 1; the rest are shown so the
// product's shape is visible early, but marked "Segera" until their phase.
const NAV_ITEMS: NavItem[] = [
  { label: "Ringkasan", href: "/dashboard", available: true },
  { label: "Lowongan", href: "/dashboard/jobs", roles: ["admin", "recruiter"], available: true },
  {
    label: "Kandidat",
    href: "/dashboard/candidates",
    roles: ["admin", "recruiter", "hiring_manager"],
    available: false,
  },
  { label: "Log Aktivitas", href: "/dashboard/activity", roles: ["admin"], available: true },
  { label: "Manajemen User", href: "/dashboard/users", roles: ["admin"], available: true },
];

const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Admin",
  recruiter: "Recruiter",
  hiring_manager: "Hiring Manager",
  interviewer: "Interviewer",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <DashboardShell>{children}</DashboardShell>
    </RequireAuth>
  );
}

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  async function handleLogout() {
    try {
      await logoutApi();
    } catch {
      // Best-effort — clear local session regardless of API result.
    }
    clear();
    router.replace("/login");
  }

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <div className="flex min-h-screen">
      <aside className="bg-sidebar text-sidebar-foreground flex w-60 shrink-0 flex-col gap-1 p-4">
        <div className="mb-4 px-2">
          <p className="font-heading text-base font-medium">HireLens AI</p>
        </div>
        {visibleItems.map((item) => {
          const active =
            item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
          if (!item.available) {
            return (
              <span
                key={item.href}
                className="text-sidebar-foreground/40 flex items-center justify-between rounded-md px-3 py-2 text-sm"
              >
                {item.label}
                <span className="text-[10px] tracking-wide uppercase">Segera</span>
              </span>
            );
          }
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "hover:bg-sidebar-accent/60 text-sidebar-foreground/90"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="border-border bg-card flex items-center justify-between border-b px-6 py-3">
          <div />
          <div className="flex items-center gap-3">
            {user && (
              <div className="text-right">
                <p className="text-sm leading-tight font-medium">{user.name}</p>
                <p className="caption leading-tight">{ROLE_LABEL[user.role]}</p>
              </div>
            )}
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Keluar
            </Button>
          </div>
        </header>
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
