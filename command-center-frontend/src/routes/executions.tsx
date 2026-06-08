import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { ExecStatus } from "@/lib/command-center-api";
import { useExecutions } from "@/lib/command-center-api";

export const Route = createFileRoute("/executions")({
  head: () => ({ meta: [{ title: "Executions — SWGI" }] }),
  component: Executions,
});

const STATUSES: (ExecStatus | "all")[] = ["all", "pending", "running", "succeeded", "failed", "rejected"];

function variantFor(s: ExecStatus) {
  return s === "succeeded" ? "success" : s === "running" ? "info" : s === "pending" ? "muted" : s === "failed" ? "destructive" : "destructive";
}

function Executions() {
  const [tab, setTab] = useState<string>("all");
  const { data: executions } = useExecutions();
  const [active, setActive] = useState<(typeof executions)[number] | null>(null);
  const filtered = executions.filter((e) => tab === "all" || e.status === tab);

  return (
    <>
      <PageHeader title="Executions" description="Operator-enforced changes against governed workloads" />
      <div className="space-y-4 p-6">
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="h-8">
            {STATUSES.map((s) => <TabsTrigger key={s} value={s} className="text-xs">{s}</TabsTrigger>)}
          </TabsList>
        </Tabs>
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left">Execution</th>
                <th className="px-4 py-2 text-left">Receipt</th>
                <th className="px-4 py-2 text-left">Cluster</th>
                <th className="px-4 py-2 text-left">Namespace / Workload</th>
                <th className="px-4 py-2 text-left">Action</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Created</th>
                <th className="px-4 py-2 text-left">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((e) => (
                <tr key={e.id} className="cursor-pointer hover:bg-muted/30" onClick={() => setActive(e)}>
                  <td className="px-4 py-2 font-mono text-[11px]">{e.id}</td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{e.receiptId}</td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{e.cluster}</td>
                  <td className="px-4 py-2 text-muted-foreground">{e.namespace}/{e.workload}</td>
                  <td className="px-4 py-2 text-muted-foreground">{e.action}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={variantFor(e.status) as any}>{e.status}</StatusBadge></td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{e.createdAt}</td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{e.updatedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <Sheet open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        <SheetContent className="w-[480px] sm:max-w-md overflow-y-auto">
          <SheetHeader><SheetTitle className="text-sm">Execution detail</SheetTitle></SheetHeader>
          {active && (
            <div className="mt-4 space-y-4 text-xs">
              <div className="font-mono text-[11px] text-muted-foreground">{active.id}</div>
              <div className="grid grid-cols-2 gap-2">
                <Box k="Status" v={<StatusBadge dot variant={variantFor(active.status) as any}>{active.status}</StatusBadge>} />
                <Box k="Action" v={active.action} />
                <Box k="Receipt" v={active.receiptId} mono />
                <Box k="Cluster" v={active.cluster} mono />
                <Box k="Namespace" v={active.namespace} />
                <Box k="Workload" v={active.workload} />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Payload hash</div>
                <div className="mt-1 break-all rounded-md border border-border bg-muted/30 p-2 font-mono text-[11px]">{active.payloadHash}</div>
              </div>
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-muted-foreground">Operator status history</div>
                <ol className="space-y-1.5 border-l border-border pl-4">
                  <li><div className="text-foreground">accepted</div><div className="text-muted-foreground">{active.createdAt} · operator pulled execution</div></li>
                  <li><div className="text-foreground">running</div><div className="text-muted-foreground">{active.updatedAt} · enforcement in progress</div></li>
                  <li><div className="text-foreground">{active.status}</div><div className="text-muted-foreground">just now · final state reported</div></li>
                </ol>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function Box({ k, v, mono }: { k: string; v: React.ReactNode; mono?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className={`mt-0.5 ${mono ? "font-mono text-[11px]" : ""}`}>{v}</div>
    </div>
  );
}
