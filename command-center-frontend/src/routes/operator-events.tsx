import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Input } from "@/components/ui/input";
import { useOperatorEvents } from "@/lib/command-center-api";
import { RequirePermission } from "@/lib/auth";

export const Route = createFileRoute("/operator-events")({
  head: () => ({ meta: [{ title: "Operator Events — SWGI" }] }),
  component: OperatorEvents,
});

function OperatorEvents() {
  return (
    <RequirePermission permission="operator:read">
      <OperatorEventsContent />
    </RequirePermission>
  );
}

function OperatorEventsContent() {
  const { data: operatorEvents } = useOperatorEvents();
  return (
    <>
      <PageHeader title="Operator Events" description="In-cluster enforcement status reports" />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Filter by cluster, namespace, workload, receipt…" className="h-8 max-w-sm text-xs" />
        </div>
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Event</th><th className="px-4 py-2 text-left">Receipt</th><th className="px-4 py-2 text-left">Cluster</th><th className="px-4 py-2 text-left">Namespace / Workload</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-left">Message</th><th className="px-4 py-2 text-left">When</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {operatorEvents.map((e) => {
                const failed = e.status !== "applied";
                return (
                  <tr key={e.id} className={failed ? "bg-destructive/5" : ""}>
                    <td className="px-4 py-2 font-mono text-[11px]">{e.id}</td>
                    <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{e.receipt}</td>
                    <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{e.cluster}</td>
                    <td className="px-4 py-2 text-muted-foreground">{e.namespace}/{e.workload}</td>
                    <td className="px-4 py-2"><StatusBadge dot variant={e.status === "applied" ? "success" : e.status === "rejected" ? "destructive" : "warning"}>{e.status}</StatusBadge></td>
                    <td className="px-4 py-2 text-muted-foreground">{e.message}</td>
                    <td className="px-4 py-2 tabular-nums text-muted-foreground">{e.at}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
