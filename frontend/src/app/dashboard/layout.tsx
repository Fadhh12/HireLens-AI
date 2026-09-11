"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  Briefcase,
  History,
  LayoutDashboard,
  MenuIcon,
  UserCog,
  Users,
  XIcon,
} from "lucide-react";

import { Logomark } from "@/components/logomark";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { logout as logoutApi } from "@/lib/auth/api";
import { useAuthStore } from "@/lib/auth/store";
import type { UserRole } from "@/lib/auth/types";

interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  roles?: UserRole[];
  available: boolean;
}

// Full IA per UI/UX Flow §3 (Screen Inventory) — only Overview and User
// Management are actually built in Phase 1; the rest are shown so the
// product's shape is visible early, but marked "Segera" until their phase.
const NAV_ITEMS: NavItem[] = [
  { label: "Ringkasan", href: "/dashboard", icon: LayoutDashboard, available: true },
  { label: "Lowongan", href: "/dashboard/jobs", icon: Briefcase, roles: ["admin", "recruiter"], available: true },
  {
    label: "Kandidat",
    href: "/dashboard/candidates",
    icon: Users,
    roles: ["admin", "recruiter", "hiring_manager"],
    available: true,
  },
  { label: "Log Aktivitas", href: "/dashboard/activity", icon: History, roles: ["admin"], available: true },
  { label: "Manajemen User", href: "/dashboard/users", icon: UserCog, roles: ["admin"], available: true },
];

const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Admin",
  recruiter: "Recruiter",
  hiring_manager: "Hiring Manager",
  interviewer: "Interviewer",
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}

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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

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

  const sidebarContent = (
    <>
      <div className="mb-5 flex items-center justify-between px-2">
        <div className="flex items-center gap-2.5">
          <Logomark />
          <p className="font-heading text-base font-medium">HireLens AI</p>
        </div>
        <button
          type="button"
          className="text-sidebar-foreground/70 md:hidden"
          onClick={() => setMobileNavOpen(false)}
          aria-label="Tutup menu"
        >
          <XIcon className="size-5" />
        </button>
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
              <span className="flex items-center gap-2.5">
                <item.icon className="size-4" strokeWidth={1.75} />
                {item.label}
              </span>
              <span className="text-[10px] tracking-wide uppercase">Segera</span>
            </span>
          );
        }
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileNavOpen(false)}
            className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "hover:bg-sidebar-accent/60 text-sidebar-foreground/90"
            }`}
          >
            <item.icon className="size-4" strokeWidth={1.75} />
            {item.label}
          </Link>
        );
      })}
    </>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop/tablet: fixed sidebar. Mobile: slide-in drawer + backdrop. */}
      <aside className="bg-sidebar text-sidebar-foreground hidden w-60 shrink-0 flex-col gap-1 p-4 md:flex">
        {sidebarContent}
      </aside>

      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
          <aside className="bg-sidebar text-sidebar-foreground relative flex h-full w-64 flex-col gap-1 p-4">
            {sidebarContent}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border bg-card flex items-center justify-between gap-3 border-b px-4 py-3 md:px-6">
          <button
            type="button"
            className="text-ink-600 md:hidden"
            onClick={() => setMobileNavOpen(true)}
            aria-label="Buka menu"
          >
            <MenuIcon className="size-5" />
          </button>
          <div className="hidden md:block" />
          <div className="flex items-center gap-3">
            {user && (
              <div className="flex items-center gap-2.5">
                <div className="hidden text-right sm:block">
                  <p className="text-sm leading-tight font-medium">{user.name}</p>
                  <p className="caption leading-tight">{ROLE_LABEL[user.role]}</p>
                </div>
                <span className="bg-secondary text-primary flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-medium">
                  {initials(user.name)}
                </span>
              </div>
            )}
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Keluar
            </Button>
          </div>
        </header>
        <main className="min-w-0 flex-1 px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  );
}
