import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Copy } from "lucide-react";
import { RequirePermission, useAuth } from "@/lib/auth";
import { updateSecuritySettings, useControlPlaneSettings, type SecuritySettings } from "@/lib/command-center-api";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — SWGI" }] }),
  component: Settings,
});

function Settings() {
  return (
    <RequirePermission permission="settings:write">
      <SettingsContent />
    </RequirePermission>
  );
}

function SettingsContent() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const { data: settings } = useControlPlaneSettings();
  const [security, setSecurity] = useState<SecuritySettings | null>(settings.security ?? null);
  const canWriteSettings = auth.can("settings:write");
  const mutation = useMutation({
    mutationFn: () => security ? updateSecuritySettings(security) : Promise.resolve({ security: settings.security! }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["command-center", "settings"] }),
  });

  useEffect(() => {
    if (settings.security) setSecurity(settings.security);
  }, [settings.security]);

  const setNumber = (key: keyof SecuritySettings, value: string) => {
    setSecurity((current) => current ? { ...current, [key]: Number(value || 0) } : current);
  };

  return (
    <>
      <PageHeader
        title="Settings"
        description="Control plane configuration · cryptographic identity · retention"
        actions={canWriteSettings ? <Button size="sm" onClick={() => mutation.mutate()} disabled={!security || mutation.isPending}>{mutation.isPending ? "Saving..." : "Save settings"}</Button> : undefined}
      />
      <div className="grid gap-4 p-6 lg:grid-cols-2">
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Signing identity</h2>
            <StatusBadge dot variant="success">active</StatusBadge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Public key fingerprint</div>
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2 font-mono text-[11px]">
              <span className="flex-1 break-all">Available from Command Center signing key</span>
              <Copy className="h-3.5 w-3.5 cursor-pointer text-muted-foreground hover:text-foreground" />
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <Field k="Algorithm" v="Ed25519" />
              <Field k="Rotation" v="manual runbook" />
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Data retention</h2>
          <div className="space-y-3 text-xs">
            <NumberField label="Receipts metadata days" value={security?.receipt_retention_days} onChange={(value) => setNumber("receipt_retention_days", value)} disabled={!canWriteSettings} />
            <NumberField label="Operator event days" value={security?.operator_event_retention_days} onChange={(value) => setNumber("operator_event_retention_days", value)} disabled={!canWriteSettings} />
            <NumberField label="Audit log days" value={security?.audit_log_retention_days} onChange={(value) => setNumber("audit_log_retention_days", value)} disabled={!canWriteSettings} />
            <p className="text-muted-foreground">Customer payload bytes are never persisted. Only signed metadata, hashes, and decisions are retained.</p>
          </div>
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Rate limits</h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <NumberField label="Intent / sec" value={security?.intent_rate_limit_per_second} onChange={(value) => setNumber("intent_rate_limit_per_second", value)} disabled={!canWriteSettings} />
            <NumberField label="Operator polls / sec" value={security?.operator_poll_limit_per_second} onChange={(value) => setNumber("operator_poll_limit_per_second", value)} disabled={!canWriteSettings} />
            <NumberField label="Org admin / min" value={security?.org_admin_requests_per_minute} onChange={(value) => setNumber("org_admin_requests_per_minute", value)} disabled={!canWriteSettings} />
            <NumberField label="Burst window seconds" value={security?.burst_window_seconds} onChange={(value) => setNumber("burst_window_seconds", value)} disabled={!canWriteSettings} />
          </div>
          {mutation.isError && <div className="mt-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">Settings could not be saved.</div>}
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Security posture</h2>
          <ul className="space-y-2 text-xs text-muted-foreground">
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">HTTP-only sessions.</strong> Browser sessions are held in secure server-issued cookies.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Metadata-only.</strong> Customer payload bytes are outside the control plane boundary.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Signed Trust Receipts.</strong> Every governed decision is signed.</span></li>
            <li className="flex gap-2"><StatusBadge dot variant="success">on</StatusBadge> <span><strong className="text-foreground">Tenant isolation.</strong> Users, API keys, clusters, audit streams, and receipts are scoped by org.</span></li>
          </ul>
        </Card>
      </div>
    </>
  );
}

function NumberField({ label, value, onChange, disabled }: { label: string; value?: number; onChange: (value: string) => void; disabled: boolean }) {
  return <div><Label className="text-xs">{label}</Label><Input className="h-8 text-xs" type="number" value={value ?? 0} onChange={(event) => onChange(event.target.value)} disabled={disabled} /></div>;
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className="mt-0.5 font-mono text-[11px]">{v}</div>
    </div>
  );
}
