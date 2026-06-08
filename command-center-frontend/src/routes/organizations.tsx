import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Plus } from "lucide-react";
import { orgs } from "@/lib/mock-data";

export const Route = createFileRoute("/organizations")({
  head: () => ({ meta: [{ title: "Organizations — SWGI" }] }),
  component: Organizations,
});

function Organizations() {
  const [q, setQ] = useState("");
  const filtered = orgs.filter((o) => o.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <PageHeader
        title="Organizations"
        description="Tenant boundaries · isolated execution and metering"
        actions={
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm"><Plus className="mr-1 h-4 w-4" />New organization</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create organization</DialogTitle></DialogHeader>
              <div className="space-y-3 text-sm">
                <div><Label>Name</Label><Input placeholder="Acme Corp" /></div>
                <div><Label>Plan</Label><Input placeholder="Starter / Growth / Enterprise" /></div>
                <p className="text-xs text-muted-foreground">A new tenant boundary will be provisioned with isolated signing keys.</p>
              </div>
              <DialogFooter><Button>Create</Button></DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />
      <div className="space-y-4 p-6">
        <div className="flex gap-2">
          <Input placeholder="Search organizations…" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm h-8" />
        </div>
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Organization</th><th className="px-4 py-2 text-left">Plan</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-right">Clusters</th><th className="px-4 py-2 text-right">Monthly executions</th><th className="px-4 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((o) => (
                <tr key={o.id} className="hover:bg-muted/30">
                  <td className="px-4 py-2"><div className="font-medium text-foreground">{o.name}</div><div className="font-mono text-[10px] text-muted-foreground">{o.id}</div></td>
                  <td className="px-4 py-2 text-muted-foreground">{o.plan}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={o.status === "active" ? "success" : o.status === "trial" ? "info" : "destructive"}>{o.status}</StatusBadge></td>
                  <td className="px-4 py-2 text-right tabular-nums">{o.clusters}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{o.monthlyExecutions.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right"><Button size="sm" variant="ghost">Open</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
