import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { policies } from "@/lib/mock-data";

export const Route = createFileRoute("/policies")({
  head: () => ({ meta: [{ title: "Policies — SWGI" }] }),
  component: Policies,
});

function Policies() {
  return (
    <>
      <PageHeader title="Policies" description="Governance rules evaluated before each Trust Receipt is issued" />
      <div className="space-y-4 p-6">
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Policy</th><th className="px-4 py-2 text-left">Scope</th><th className="px-4 py-2 text-right">Attached</th><th className="px-4 py-2 text-left">Version</th><th className="px-4 py-2 text-left">Status</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {policies.map((p) => (
                <tr key={p.id} className="hover:bg-muted/30">
                  <td className="px-4 py-2"><div className="font-medium">{p.name}</div><div className="font-mono text-[10px] text-muted-foreground">{p.id}</div></td>
                  <td className="px-4 py-2 text-muted-foreground">{p.scope}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{p.attached}</td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">v{p.version}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant="success">enforced</StatusBadge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
