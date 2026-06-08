import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { orgs, clusters, dashboardStats } from "@/lib/mock-data";

export const Route = createFileRoute("/usage")({
  head: () => ({ meta: [{ title: "Usage & Billing — SWGI" }] }),
  component: Usage,
});

function Usage() {
  const s = dashboardStats;
  const usagePct = Math.round((s.monthlyUsage / s.planLimit) * 100);

  return (
    <>
      <PageHeader
        title="Usage & Billing"
        description="Per-tenant metered execution counts · plan limits"
        actions={
          <Select defaultValue="2026-05">
            <SelectTrigger className="h-8 w-44 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="2026-05" className="text-xs">May 2026 (current)</SelectItem>
              <SelectItem value="2026-04" className="text-xs">April 2026</SelectItem>
              <SelectItem value="2026-03" className="text-xs">March 2026</SelectItem>
            </SelectContent>
          </Select>
        }
      />
      <div className="space-y-6 p-6">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Plan usage</div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">{s.monthlyUsage.toLocaleString()} <span className="text-sm font-normal text-muted-foreground">/ {s.planLimit.toLocaleString()} executions</span></div>
            </div>
            <StatusBadge variant={usagePct > 90 ? "destructive" : usagePct > 75 ? "warning" : "info"}>{usagePct}% used</StatusBadge>
          </div>
          <Progress value={usagePct} className="mt-4 h-2" />
          {usagePct > 90 && (
            <div className="mt-3 rounded-md border border-destructive/20 bg-destructive/5 p-2 text-xs text-destructive">
              Approaching plan limit — overage rates apply beyond {s.planLimit.toLocaleString()} executions.
            </div>
          )}
        </Card>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="p-4"><Stat label="Allowed" value={s.allow} variant="success" /></Card>
          <Card className="p-4"><Stat label="Modified" value={s.modify} variant="warning" /></Card>
          <Card className="p-4"><Stat label="Denied" value={s.deny} variant="destructive" /></Card>
        </div>

        <Card className="p-0">
          <div className="border-b border-border px-4 py-3 text-sm font-semibold">Usage by organization</div>
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Org</th><th className="px-4 py-2 text-left">Plan</th><th className="px-4 py-2 text-right">Executions</th><th className="px-4 py-2 text-right">Allowed</th><th className="px-4 py-2 text-right">Denied</th><th className="px-4 py-2 text-right">Modified</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {orgs.map((o, i) => (
                <tr key={o.id}>
                  <td className="px-4 py-2"><div className="font-medium">{o.name}</div><div className="font-mono text-[10px] text-muted-foreground">{o.id}</div></td>
                  <td className="px-4 py-2 text-muted-foreground">{o.plan}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{o.monthlyExecutions.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-success">{Math.round(o.monthlyExecutions * 0.91).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-destructive">{Math.round(o.monthlyExecutions * 0.05).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-warning-foreground">{Math.round(o.monthlyExecutions * 0.04).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="p-0">
          <div className="border-b border-border px-4 py-3 text-sm font-semibold">Usage by cluster</div>
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Cluster</th><th className="px-4 py-2 text-left">Runtime</th><th className="px-4 py-2 text-right">Executions</th><th className="px-4 py-2 text-right">Top namespace</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {clusters.map((c, i) => (
                <tr key={c.id}>
                  <td className="px-4 py-2 font-mono text-[11px]">{c.name}</td>
                  <td className="px-4 py-2 text-muted-foreground">{c.runtime}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{(8000 + i * 1840).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-muted-foreground">payments</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}

function Stat({ label, value, variant }: { label: string; value: number; variant: "success" | "warning" | "destructive" }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
        <StatusBadge variant={variant}>{label.toLowerCase()}</StatusBadge>
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums">{value.toLocaleString()}</div>
    </div>
  );
}
