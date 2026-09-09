"use client";

import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/require-auth";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listActivityLogs } from "@/lib/activity/api";
import type { ActivityLogEntry } from "@/lib/activity/types";

const ACTION_LABEL: Record<string, string> = {
  status_changed: "Ubah Status Kandidat",
};

export default function ActivityLogPage() {
  return (
    <RequireAuth allowedRoles={["admin"]}>
      <ActivityLogContent />
    </RequireAuth>
  );
}

function ActivityLogContent() {
  const [logs, setLogs] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listActivityLogs()
      .then(setLogs)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1>Log Aktivitas</h1>
        <p className="caption">Riwayat perubahan status kandidat (FR-7.3).</p>
      </div>

      <div className="border-border bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Waktu</TableHead>
              <TableHead>Aktor</TableHead>
              <TableHead>Aksi</TableHead>
              <TableHead>Nilai Lama</TableHead>
              <TableHead>Nilai Baru</TableHead>
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
            {!loading && logs.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-ink-400 text-center">
                  Belum ada aktivitas tercatat.
                </TableCell>
              </TableRow>
            )}
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="text-ink-600">
                  {new Date(log.created_at).toLocaleString("id-ID")}
                </TableCell>
                <TableCell>{log.actor_name}</TableCell>
                <TableCell>{ACTION_LABEL[log.action] ?? log.action}</TableCell>
                <TableCell className="text-ink-600">{log.old_value ?? "—"}</TableCell>
                <TableCell className="text-ink-600">{log.new_value ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
