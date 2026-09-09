"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/require-auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError } from "@/lib/api/client";
import type { User, UserRole } from "@/lib/auth/types";
import { createUser, listUsers, updateUser } from "@/lib/users/api";

const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Admin",
  recruiter: "Recruiter",
  hiring_manager: "Hiring Manager",
  interviewer: "Interviewer",
};

const ROLE_OPTIONS: UserRole[] = ["admin", "recruiter", "hiring_manager", "interviewer"];

export default function UsersPage() {
  return (
    <RequireAuth allowedRoles={["admin"]}>
      <UsersPageContent />
    </RequireAuth>
  );
}

function UsersPageContent() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setUsers(await listUsers());
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal memuat daftar user");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleToggleActive(user: User) {
    try {
      const updated = await updateUser(user.id, { is_active: !user.is_active });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      toast.success(updated.is_active ? "Akun diaktifkan kembali" : "Akun dinonaktifkan");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal mengubah status akun");
    }
  }

  async function handleRoleChange(user: User, role: UserRole) {
    try {
      const updated = await updateUser(user.id, { role });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      toast.success("Role diperbarui");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Gagal mengubah role");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1>Manajemen User</h1>
          <p className="caption">Kelola akun tim dan role akses (SRS §2).</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button>+ Tambah User</Button>} />
          <CreateUserDialog
            onCreated={(u) => {
              setUsers((prev) => [u, ...prev]);
              setDialogOpen(false);
            }}
          />
        </Dialog>
      </div>

      <div className="border-border bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nama</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={5} className="text-ink-400 text-center">
                  Memuat...
                </TableCell>
              </TableRow>
            )}
            {!loading && users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-ink-400 text-center">
                  Belum ada user.
                </TableCell>
              </TableRow>
            )}
            {users.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="font-medium">{u.name}</TableCell>
                <TableCell className="text-ink-600">{u.email}</TableCell>
                <TableCell>
                  <Select value={u.role} onValueChange={(v) => handleRoleChange(u, v as UserRole)}>
                    <SelectTrigger size="sm" className="w-44">
                      <SelectValue>{ROLE_LABEL[u.role]}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {ROLE_OPTIONS.map((r) => (
                        <SelectItem key={r} value={r}>
                          {ROLE_LABEL[r]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Badge
                    className={
                      u.is_active
                        ? "bg-success-100 text-success-700"
                        : "bg-danger-100 text-danger-700"
                    }
                  >
                    {u.is_active ? "Aktif" : "Nonaktif"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm" onClick={() => handleToggleActive(u)}>
                    {u.is_active ? "Nonaktifkan" : "Aktifkan"}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function CreateUserDialog({ onCreated }: { onCreated: (user: User) => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("recruiter");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await createUser({ name, email, password, role });
      onCreated(user);
      setName("");
      setEmail("");
      setPassword("");
      setRole("recruiter");
      toast.success(`User ${user.name} dibuat`);
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : "Gagal membuat user");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Tambah User Baru</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="new-name">Nama</Label>
          <Input id="new-name" required value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="new-email">Email</Label>
          <Input
            id="new-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="new-password">Password sementara</Label>
          <Input
            id="new-password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min. 8 karakter, huruf + angka"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="new-role">Role</Label>
          <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
            <SelectTrigger id="new-role" className="w-full">
              <SelectValue>{ROLE_LABEL[role]}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {ROLE_OPTIONS.map((r) => (
                <SelectItem key={r} value={r}>
                  {ROLE_LABEL[r]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error && (
          <p className="text-danger-700 bg-danger-100 rounded-md px-3 py-2 text-sm">{error}</p>
        )}

        <DialogFooter>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Menyimpan..." : "Simpan"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
