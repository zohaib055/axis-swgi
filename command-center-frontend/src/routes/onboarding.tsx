import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RequirePermission } from "@/lib/auth";
import { createOrganization, createUser, registerCluster } from "@/lib/command-center-api";

export const Route = createFileRoute("/onboarding")({
  head: () => ({ meta: [{ title: "Onboarding — SWGI" }] }),
  component: Onboarding,
});

function Onboarding() {
  return (
    <RequirePermission permission="org:write">
      <OnboardingContent />
    </RequirePermission>
  );
}

function OnboardingContent() {
  const queryClient = useQueryClient();
  const [orgId, setOrgId] = useState("");
  const [orgName, setOrgName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [clusterId, setClusterId] = useState("");
  const [clusterName, setClusterName] = useState("");
  const [runtime, setRuntime] = useState("kubernetes");
  const [install, setInstall] = useState<Record<string, string> | null>(null);
  const mutation = useMutation({
    mutationFn: async () => {
      await createOrganization({ orgId, displayName: orgName });
      await createUser({ email: adminEmail, password: adminPassword, role: "org_admin", orgId });
      const cluster = await registerCluster({ orgId, clusterId, displayName: clusterName, runtime });
      return cluster.install;
    },
    onSuccess: (nextInstall) => {
      setInstall(nextInstall);
      void queryClient.invalidateQueries({ queryKey: ["command-center"] });
    },
  });

  return (
    <>
      <PageHeader title="Customer onboarding" description="Create tenant, first admin, and cluster install configuration" />
      <div className="grid gap-4 p-6 lg:grid-cols-[1fr_1fr]">
        <Card className="p-4">
          <form
            className="space-y-4 text-sm"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate();
            }}
          >
            <section className="space-y-3">
              <h2 className="text-sm font-semibold">Customer org</h2>
              <div><Label>Org ID</Label><Input value={orgId} onChange={(event) => setOrgId(event.target.value)} placeholder="axis" required /></div>
              <div><Label>Display name</Label><Input value={orgName} onChange={(event) => setOrgName(event.target.value)} placeholder="Axis" required /></div>
            </section>
            <section className="space-y-3">
              <h2 className="text-sm font-semibold">First customer admin</h2>
              <div><Label>Email</Label><Input value={adminEmail} onChange={(event) => setAdminEmail(event.target.value)} type="email" required /></div>
              <div><Label>Temporary password</Label><Input value={adminPassword} onChange={(event) => setAdminPassword(event.target.value)} type="password" minLength={12} required /></div>
            </section>
            <section className="space-y-3">
              <h2 className="text-sm font-semibold">First cluster</h2>
              <div><Label>Cluster ID</Label><Input value={clusterId} onChange={(event) => setClusterId(event.target.value)} placeholder="axis-prod-001" required /></div>
              <div><Label>Cluster name</Label><Input value={clusterName} onChange={(event) => setClusterName(event.target.value)} placeholder="Axis production" required /></div>
              <div>
                <Label>Runtime</Label>
                <Select value={runtime} onValueChange={setRuntime}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="kubernetes">Kubernetes</SelectItem>
                    <SelectItem value="openshift">OpenShift</SelectItem>
                    <SelectItem value="gke">GKE</SelectItem>
                    <SelectItem value="eks">EKS</SelectItem>
                    <SelectItem value="aks">AKS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </section>
            {mutation.isError && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">Onboarding failed. Check duplicate org/user/cluster values.</div>}
            <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Provisioning..." : "Provision customer"}</Button>
          </form>
        </Card>
        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Operator install output</h2>
          {install ? (
            <pre className="max-h-[560px] overflow-auto rounded-md border border-border bg-muted/40 p-3 text-xs">{Object.entries(install).map(([key, value]) => `${key}=${JSON.stringify(value)}`).join("\n")}</pre>
          ) : (
            <div className="rounded-md border border-border bg-muted/30 p-4 text-sm text-muted-foreground">Provision a customer to generate the cluster install configuration.</div>
          )}
        </Card>
      </div>
    </>
  );
}
