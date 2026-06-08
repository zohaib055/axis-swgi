import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Copy } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — SWGI" }] }),
  component: Settings,
});

function Settings() {
  return (
    <>
      <PageHeader title="Settings" description="Control plane configuration · cryptographic identity · retention" />
      <div className="grid gap-4 p-6 lg:grid-cols-2">
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Signing identity</h2>
            <StatusBadge dot variant="success">active</StatusBadge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Public key fingerprint</div>
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2 font-mono text-[11px]">
              <span className="flex-1 break-all">SHA256:8f:2a:c1:b3:e8:4d:7c:a9:01:8f:7d:3e:2c:1b:6a:9c:5d:4e:3f:47</span>
              <Copy className="h-3.5 w-3.5 cursor-pointer text-muted-foreground hover:text-foreground" />
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <Field k="Algorithm" v="Ed25519" />
              <Field k="Rotated" v="2026-02-14" />
            </div>
            <Button variant="outline" size="sm" className="mt-3">Rotate signing key</Button>
          </div>
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Data retention</h2>
          <div className="space-y-3 text-xs">
            <div><Label className="text-xs">Receipts (metadata)</Label><Input className="h-8 text-xs" defaultValue="365 days" /></div>
            <div><Label className="text-xs">Operator events</Label><Input className="h-8 text-xs" defaultValue="90 days" /></div>
            <div><Label className="text-xs">Audit logs</Label><Input className="h-8 text-xs" defaultValue="2555 days (7y)" /></div>
            <p className="text-muted-foreground">Customer payload bytes are never persisted. Only signed metadata, hashes, and decisions are retained.</p>
          </div>
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Rate limits</h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div><Label className="text-xs">Intent submissions / sec</Label><Input className="h-8 text-xs" defaultValue="500" /></div>
            <div><Label className="text-xs">Operator polls / sec</Label><Input className="h-8 text-xs" defaultValue="2000" /></div>
            <div><Label className="text-xs">Org admin requests / min</Label><Input className="h-8 text-xs" defaultValue="600" /></div>
            <div><Label className="text-xs">Burst window</Label><Input className="h-8 text-xs" defaultValue="10s" /></div>
          </div>
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Security posture</h2>
          <ul className="space-y-2 text-xs text-muted-foreground">
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Metadata-only.</strong> The control plane never receives or stores customer payload bytes.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Signed Trust Receipts.</strong> Every governed decision is signed by the org-scoped key.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Tenant isolation.</strong> Per-org signing keys, audit streams, and rate limits.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Operator enforcement.</strong> Execution decisions are enforced in-cluster by the SWGI Operator.</span></li>
          </ul>
        </Card>
      </div>
    </>
  );
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className="mt-0.5 font-mono text-[11px]">{v}</div>
    </div>
  );
}
