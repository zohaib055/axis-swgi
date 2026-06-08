import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff, Copy } from "lucide-react";
import type { Runtime } from "@/lib/command-center-api";
import { useClusters } from "@/lib/command-center-api";
import { RequirePermission, useAuth } from "@/lib/auth";

export const Route = createFileRoute("/clusters")({
  head: () => ({ meta: [{ title: "Clusters — SWGI" }] }),
  component: Clusters,
});

const RUNTIMES: (Runtime | "all")[] = ["all", "Kubernetes", "OpenShift", "GKE", "EKS", "AKS", "on-prem"];

function Clusters() {
  return (
    <RequirePermission permission="cluster:read">
      <ClustersContent />
    </RequirePermission>
  );
}

function ClustersContent() {
  const [runtime, setRuntime] = useState<string>("all");
  const { data: clusters } = useClusters();
  const auth = useAuth();
  const canWriteCluster = auth.can("cluster:write");
  const [active, setActive] = useState<(typeof clusters)[number] | null>(null);
  const [showToken, setShowToken] = useState(false);

  const filtered = useMemo(
    () => clusters.filter((c) => runtime === "all" || c.runtime === runtime),
    [runtime],
  );

  return (
    <>
      <PageHeader
        title="Clusters"
        description="Registered clusters · Operator-enforced execution governance"
      />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Select value={runtime} onValueChange={setRuntime}>
            <SelectTrigger className="h-8 w-44 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              {RUNTIMES.map((r) => <SelectItem key={r} value={r} className="text-xs">{r === "all" ? "All runtimes" : r}</SelectItem>)}
            </SelectContent>
          </Select>
          <Input placeholder="Search clusters…" className="h-8 max-w-xs text-xs" />
        </div>
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left">Cluster</th>
                <th className="px-4 py-2 text-left">Org</th>
                <th className="px-4 py-2 text-left">Runtime</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Operator</th>
                <th className="px-4 py-2 text-left">Last heartbeat</th>
                <th className="px-4 py-2 text-right">Namespaces</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((c) => (
                <tr key={c.id} className="cursor-pointer hover:bg-muted/30" onClick={() => { setActive(c); setShowToken(false); }}>
                  <td className="px-4 py-2"><div className="font-medium">{c.name}</div><div className="font-mono text-[10px] text-muted-foreground">{c.id}</div></td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{c.org}</td>
                  <td className="px-4 py-2 text-muted-foreground">{c.runtime}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={c.status === "healthy" ? "success" : c.status === "degraded" ? "warning" : "destructive"}>{c.status}</StatusBadge></td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{c.operatorVersion}</td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{c.lastHeartbeat}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{c.namespaces}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <Sheet open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        <SheetContent className="w-[480px] sm:max-w-md overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="text-sm">Cluster registration</SheetTitle>
          </SheetHeader>
          {active && (
            <div className="mt-4 space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">{active.name}</div>
                  <div className="font-mono text-[11px] text-muted-foreground">{active.id}</div>
                </div>
                <StatusBadge dot variant={active.status === "healthy" ? "success" : active.status === "degraded" ? "warning" : "destructive"}>{active.status}</StatusBadge>
              </div>

              <div className="rounded-md border border-border bg-muted/30 p-3 font-mono text-[11px]">
                <Field label="COMMAND_CENTER_URL" value="https://api.swgi.io" />
                <Field label="ORG_ID" value={active.org} />
                <Field label="CLUSTER_ID" value={active.id} />
                <Field
                  label="OPERATOR_TOKEN"
                  value={showToken ? "swgi_op_3f9c2a8b71e44d0c91ab74f6c1d2e5a8" : "••••••••••••••••••••••••••••"}
                  trailing={
                    <button onClick={() => setShowToken((s) => !s)} className="text-muted-foreground hover:text-foreground">
                      {showToken ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    </button>
                  }
                />
                <Field label="PUBLIC_SIGNING_KEY_PEM" value="-----BEGIN PUBLIC KEY-----…MIIBIjANBgkq…—END—" />
              </div>

              <div className="rounded-md border border-info/20 bg-info/5 p-3 text-info">
                Operator enforces signed Trust Receipts in-cluster. The control plane sees only metadata.
              </div>

              {canWriteCluster && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">Rotate token</Button>
                  <Button size="sm" variant="ghost">Download manifest</Button>
                </div>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function Field({ label, value, trailing }: { label: string; value: string; trailing?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-2 border-b border-border/60 py-1.5 last:border-0">
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="truncate text-foreground">{value}</div>
      </div>
      <div className="flex items-center gap-1">
        {trailing}
        <button className="text-muted-foreground hover:text-foreground"><Copy className="h-3.5 w-3.5" /></button>
      </div>
    </div>
  );
}
