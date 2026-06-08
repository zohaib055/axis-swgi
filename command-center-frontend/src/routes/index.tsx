import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useClusters, useOperatorEvents, useReceipts, useUsage } from "@/lib/command-center-api";
import { Activity, Server, AlertTriangle, ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [{ title: "Dashboard — SWGI Command Center" }],
  }),
  component: Dashboard,
});

function Stat({
  label,
  value,
  hint,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon: any;
  tone?: "default" | "warning" | "success" | "destructive";
}) {
  const toneClass =
    tone === "warning"
      ? "text-warning-foreground"
      : tone === "destructive"
      ? "text-destructive"
      : tone === "success"
      ? "text-success"
      : "text-foreground";
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className={`mt-2 text-2xl font-semibold tabular-nums ${toneClass}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
    </Card>
  );
}

function Dashboard() {
  const { data: s } = useUsage();
  const { data: receipts } = useReceipts();
  const { data: operatorEvents } = useOperatorEvents();
  const { data: clusters } = useClusters();
  const usagePct = s.planLimit > 0 ? Math.round((s.monthlyUsage / s.planLimit) * 100) : 0;

  return (
    <>
      <PageHeader
        title="Command Center"
        description="Cluster execution governance · current billing period"
      />
      <div className="space-y-6 p-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Total executions" value={s.totalExecutions.toLocaleString()} hint="last 30 days" icon={Activity} />
          <Stat label="Active clusters" value={s.activeClusters} hint={`${s.degradedOperators} degraded · ${s.disconnectedOperators} disconnected`} icon={Server} />
          <Stat label="Denied attempts" value={s.deny.toLocaleString()} hint="policy-blocked" icon={ShieldCheck} tone="destructive" />
          <Stat label="Operator alerts" value={s.degradedOperators + s.disconnectedOperators} hint="needs attention" icon={AlertTriangle} tone="warning" />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="p-4 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Decision distribution</h2>
              <span className="text-xs text-muted-foreground">last 30d</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <DecisionBar label="ALLOW" value={s.allow} total={s.totalExecutions} variant="allow" />
              <DecisionBar label="MODIFY" value={s.modify} total={s.totalExecutions} variant="modify" />
              <DecisionBar label="DENY" value={s.deny} total={s.totalExecutions} variant="deny" />
            </div>
          </Card>
          <Card className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Plan usage</h2>
              <StatusBadge variant={usagePct > 90 ? "destructive" : "info"}>{usagePct}%</StatusBadge>
            </div>
            <Progress value={usagePct} className="h-2" />
            <div className="mt-2 flex justify-between text-xs text-muted-foreground tabular-nums">
              <span>{s.monthlyUsage.toLocaleString()} executions</span>
              <span>limit {s.planLimit.toLocaleString()}</span>
            </div>
            <div className="mt-4 space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between"><span>Plan</span><span className="text-foreground">Enterprise</span></div>
              <div className="flex justify-between"><span>Renews</span><span className="text-foreground">May 28, 2026</span></div>
            </div>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="p-0">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Recent receipts</h2>
              <span className="text-xs text-muted-foreground">metadata only</span>
            </div>
            <div className="divide-y divide-border text-xs">
              {receipts.slice(0, 6).map((r) => (
                <div key={r.id} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 px-4 py-2">
                  <div className="min-w-0">
                    <div className="truncate font-mono text-[11px] text-foreground">{r.id}</div>
                    <div className="truncate text-muted-foreground">{r.namespace}/{r.workload}</div>
                  </div>
                  <StatusBadge variant={r.decision === "ALLOW" ? "allow" : r.decision === "DENY" ? "deny" : "modify"}>
                    {r.decision}
                  </StatusBadge>
                  <span className="text-muted-foreground tabular-nums">{r.createdAt}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-0">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Operator events</h2>
              <span className="text-xs text-muted-foreground">enforcement reports</span>
            </div>
            <div className="divide-y divide-border text-xs">
              {operatorEvents.slice(0, 6).map((e) => (
                <div key={e.id} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 px-4 py-2">
                  <div className="min-w-0">
                    <div className="truncate font-mono text-[11px] text-foreground">{e.cluster}</div>
                    <div className="truncate text-muted-foreground">{e.message}</div>
                  </div>
                  <StatusBadge variant={e.status === "applied" ? "success" : e.status === "rejected" ? "destructive" : "warning"}>
                    {e.status}
                  </StatusBadge>
                  <span className="text-muted-foreground tabular-nums">{e.at}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card className="p-0">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold">Cluster operator health</h2>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Cluster</th><th className="px-4 py-2 text-left">Runtime</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-left">Operator</th><th className="px-4 py-2 text-left">Heartbeat</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {clusters.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-2 font-mono text-[11px]">{c.name}</td>
                  <td className="px-4 py-2 text-muted-foreground">{c.runtime}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={c.status === "healthy" ? "success" : c.status === "degraded" ? "warning" : "destructive"}>{c.status}</StatusBadge></td>
                  <td className="px-4 py-2 text-muted-foreground tabular-nums">{c.operatorVersion}</td>
                  <td className="px-4 py-2 text-muted-foreground tabular-nums">{c.lastHeartbeat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}

function DecisionBar({ label, value, total, variant }: { label: string; value: number; total: number; variant: "allow" | "deny" | "modify" }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  const colorVar = variant === "allow" ? "bg-success" : variant === "deny" ? "bg-destructive" : "bg-warning";
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <StatusBadge variant={variant}>{label}</StatusBadge>
        <span className="tabular-nums text-muted-foreground">{pct}%</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div className={`h-full ${colorVar}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1 text-xs tabular-nums text-foreground">{value.toLocaleString()}</div>
    </div>
  );
}
