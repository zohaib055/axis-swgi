import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { receipts } from "@/lib/mock-data";

export const Route = createFileRoute("/receipts")({
  head: () => ({ meta: [{ title: "Receipts — SWGI" }] }),
  component: Receipts,
});

function Receipts() {
  const [decision, setDecision] = useState("all");
  const [active, setActive] = useState<typeof receipts[number] | null>(null);
  const filtered = useMemo(
    () => receipts.filter((r) => decision === "all" || r.decision === decision),
    [decision],
  );

  return (
    <>
      <PageHeader
        title="Trust Receipts"
        description="Signed metadata-only attestations of every governed execution"
      />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Search receipt id, namespace, workload…" className="h-8 max-w-xs text-xs" />
          <Select value={decision} onValueChange={setDecision}>
            <SelectTrigger className="h-8 w-36 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="text-xs">All decisions</SelectItem>
              <SelectItem value="ALLOW" className="text-xs">ALLOW</SelectItem>
              <SelectItem value="MODIFY" className="text-xs">MODIFY</SelectItem>
              <SelectItem value="DENY" className="text-xs">DENY</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="h-8 w-40 text-xs" />
        </div>

        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left">Receipt</th>
                <th className="px-4 py-2 text-left">Cluster</th>
                <th className="px-4 py-2 text-left">Namespace / Workload</th>
                <th className="px-4 py-2 text-left">Decision</th>
                <th className="px-4 py-2 text-left">Policy</th>
                <th className="px-4 py-2 text-left">Signature</th>
                <th className="px-4 py-2 text-left">Issued</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((r) => (
                <tr key={r.id} className="cursor-pointer hover:bg-muted/30" onClick={() => setActive(r)}>
                  <td className="px-4 py-2 font-mono text-[11px]">{r.id}</td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{r.cluster}</td>
                  <td className="px-4 py-2 text-muted-foreground">{r.namespace}/{r.workload}</td>
                  <td className="px-4 py-2"><StatusBadge variant={r.decision === "ALLOW" ? "allow" : r.decision === "DENY" ? "deny" : "modify"}>{r.decision}</StatusBadge></td>
                  <td className="px-4 py-2 text-muted-foreground">{r.policy}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant="success">verified</StatusBadge></td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{r.createdAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <Sheet open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        <SheetContent className="w-[480px] sm:max-w-md overflow-y-auto">
          <SheetHeader><SheetTitle className="text-sm">Receipt detail</SheetTitle></SheetHeader>
          {active && (
            <div className="mt-4 space-y-4 text-xs">
              <div className="font-mono text-[11px] text-muted-foreground">{active.id}</div>
              <div className="grid grid-cols-2 gap-2">
                <Meta k="Decision" v={<StatusBadge variant={active.decision === "ALLOW" ? "allow" : active.decision === "DENY" ? "deny" : "modify"}>{active.decision}</StatusBadge>} />
                <Meta k="Signature" v={<StatusBadge dot variant="success">verified</StatusBadge>} />
                <Meta k="Org" v={active.org} mono />
                <Meta k="Cluster" v={active.cluster} mono />
                <Meta k="Namespace" v={active.namespace} />
                <Meta k="Workload" v={active.workload} />
                <Meta k="Policy" v={active.policy} />
                <Meta k="Expires" v={active.expiresAt} />
                <Meta k="Enforcement" v={<StatusBadge variant={active.enforcement === "applied" ? "success" : "destructive"}>{active.enforcement}</StatusBadge>} />
                <Meta k="Issued" v={active.createdAt} />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Payload hash</div>
                <div className="mt-1 break-all rounded-md border border-border bg-muted/30 p-2 font-mono text-[11px]">{active.payloadHash}</div>
              </div>
              <div className="rounded-md border border-info/20 bg-info/5 p-3 text-info">
                Customer payload bytes are never transmitted to or stored by the control plane.
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function Meta({ k, v, mono }: { k: string; v: React.ReactNode; mono?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className={`mt-0.5 ${mono ? "font-mono text-[11px]" : ""}`}>{v}</div>
    </div>
  );
}
