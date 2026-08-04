import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { AuditLog } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await api.get("/audit");
        setLogs(response.data);
      } catch (err) {
        console.error("Failed to load audit logs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Administrative Audit Logs</h1>
        <p className="text-xs text-muted-foreground mt-1">Review system configuration overrides, workflow updates, and security logs.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : logs.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No audit logs captured.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Timestamp</th>
                    <th className="p-4">User</th>
                    <th className="p-4">Module</th>
                    <th className="p-4">Action</th>
                    <th className="p-4">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-xs">
                  {logs.map((log) => (
                    <tr key={log.audit_log_id} className="hover:bg-accent/20">
                      <td className="p-4 text-muted-foreground">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="p-4 font-bold">{log.user_email}</td>
                      <td className="p-4"><Badge variant="info">{log.module}</Badge></td>
                      <td className="p-4 font-semibold text-foreground/90">{log.action}</td>
                      <td className="p-4 text-muted-foreground">{log.ip_address || "127.0.0.1"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
export default AuditLogs;
