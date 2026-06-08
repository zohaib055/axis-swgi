import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Input } from "@/components/ui/input";
import { useAuditLogs } from "@/lib/command-center-api";
import { RequirePermission } from "@/lib/auth";

export const Route = createFileRoute("/audit-logs")({
  head: () => ({ meta: [{ title: "Audit Logs — SWGI" }] }),
  component: AuditLogs,
});

function AuditLogs() {
  return (
    <RequirePermission permission="audit:read">
      <AuditLogsContent />
    </RequirePermission>
  );
}

function AuditLogsContent() {
  const { data: auditLogs } = useAuditLogs();
  return (
    <>
      <PageHeader title="Audit Logs" description="Immutable, append-only timeline of every governed action" />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Filter by actor, action, request id…" className="h-8 max-w-sm text-xs" />
          <Input type="date" className="h-8 w-40 text-xs" />
        </div>
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Timestamp</th><th className="px-4 py-2 text-left">Actor</th><th className="px-4 py-2 text-left">Role</th><th className="px-4 py-2 text-left">Action</th><th className="px-4 py-2 text-left">Resource</th><th className="px-4 py-2 text-left">Outcome</th><th className="px-4 py-2 text-left">Request ID</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {auditLogs.map((l) => (
                <tr key={l.id}>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{l.at}</td>
                  <td className="px-4 py-2">{l.actor}</td>
                  <td className="px-4 py-2"><StatusBadge variant="muted">{l.role}</StatusBadge></td>
                  <td className="px-4 py-2 font-mono text-[11px]">{l.action}</td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{l.resource}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={l.outcome === "success" ? "success" : "destructive"}>{l.outcome}</StatusBadge></td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{l.requestId}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
