import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Copy } from "lucide-react";
import { apiKeys } from "@/lib/mock-data";

export const Route = createFileRoute("/api-keys")({
  head: () => ({ meta: [{ title: "API Keys — SWGI" }] }),
  component: ApiKeys,
});

function ApiKeys() {
  const [showGenerated, setShowGenerated] = useState(false);
  const generated = "swgi_live_47fa92c1b3e84d7ca9018f7d3e2c1b6a9c5d4e3f";

  return (
    <>
      <PageHeader
        title="API Keys"
        description="Org-scoped credentials for the control plane API and in-cluster Operators"
        actions={
          <Dialog onOpenChange={(o) => !o && setShowGenerated(false)}>
            <DialogTrigger asChild>
              <Button size="sm"><Plus className="mr-1 h-4 w-4" />New API key</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>{showGenerated ? "API key created" : "Create API key"}</DialogTitle></DialogHeader>
              {!showGenerated ? (
                <div className="space-y-3 text-sm">
                  <div><Label>Name</Label><Input placeholder="ci-deploy" /></div>
                  <div><Label>Role</Label><Input placeholder="org_admin / org_viewer / operator" /></div>
                  <div><Label>Expires</Label><Input type="date" /></div>
                </div>
              ) : (
                <div className="space-y-3 text-sm">
                  <div className="rounded-md border border-warning/30 bg-warning/10 p-3 text-xs text-warning-foreground">
                    Copy this token now. For tenant isolation, the secret is shown only once and never stored in plaintext.
                  </div>
                  <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2 font-mono text-xs">
                    <span className="flex-1 break-all">{generated}</span>
                    <button className="text-muted-foreground hover:text-foreground"><Copy className="h-4 w-4" /></button>
                  </div>
                </div>
              )}
              <DialogFooter>
                {!showGenerated ? (
                  <Button onClick={() => setShowGenerated(true)}>Create</Button>
                ) : (
                  <Button variant="outline">Done</Button>
                )}
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />
      <div className="space-y-4 p-6">
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">Name</th><th className="px-4 py-2 text-left">Org</th><th className="px-4 py-2 text-left">Role</th><th className="px-4 py-2 text-left">Created</th><th className="px-4 py-2 text-left">Last used</th><th className="px-4 py-2 text-left">Expires</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-right">Actions</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {apiKeys.map((k) => (
                <tr key={k.id}>
                  <td className="px-4 py-2"><div className="font-medium">{k.name}</div><div className="font-mono text-[10px] text-muted-foreground">{k.id}</div></td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{k.org}</td>
                  <td className="px-4 py-2"><StatusBadge variant={k.role === "org_admin" ? "info" : k.role === "operator" ? "success" : "muted"}>{k.role}</StatusBadge></td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{k.created}</td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{k.lastUsed}</td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{k.expires}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={k.status === "active" ? "success" : "destructive"}>{k.status}</StatusBadge></td>
                  <td className="px-4 py-2 text-right">
                    <Button size="sm" variant="ghost" className="h-7 text-xs">Rotate</Button>
                    <Button size="sm" variant="ghost" className="h-7 text-xs text-destructive">Revoke</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
