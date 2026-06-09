import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Copy } from "lucide-react";
import { createApiKey, revokeApiKey, rotateApiKey, useApiKeys, useOrganizations, type ApiKeyRole } from "@/lib/command-center-api";
import { RequirePermission, useAuth } from "@/lib/auth";

export const Route = createFileRoute("/api-keys")({
  head: () => ({ meta: [{ title: "API Keys — SWGI" }] }),
  component: ApiKeys,
});

function ApiKeys() {
  return (
    <RequirePermission permission="api_key:write">
      <ApiKeysContent />
    </RequirePermission>
  );
}

function ApiKeysContent() {
  const [open, setOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [role, setRole] = useState<ApiKeyRole>("org_viewer");
  const [orgId, setOrgId] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [generated, setGenerated] = useState<{ name: string; token: string } | null>(null);
  const { data: apiKeys } = useApiKeys();
  const { data: orgs } = useOrganizations();
  const auth = useAuth();
  const queryClient = useQueryClient();
  const canWriteKeys = auth.can("api_key:write");
  const availableOrgs = auth.user?.orgId ? orgs.filter((org) => org.id === auth.user?.orgId) : orgs;
  const selectedOrg = orgId || availableOrgs[0]?.id || auth.user?.orgId || "";
  const createMutation = useMutation({
    mutationFn: () => createApiKey({ orgId: selectedOrg, keyName, role, expiresAt: expiresAt || undefined }),
    onSuccess: (created) => {
      setGenerated({ name: created.name, token: created.token });
      void queryClient.invalidateQueries({ queryKey: ["command-center", "api-keys"] });
    },
  });
  const revokeMutation = useMutation({
    mutationFn: (key: { org: string; id: string }) => revokeApiKey(key.org, key.id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["command-center", "api-keys"] }),
  });
  const rotateMutation = useMutation({
    mutationFn: (key: { org: string; id: string }) => rotateApiKey(key.org, key.id),
    onSuccess: (created) => {
      setGenerated({ name: created.name, token: created.token });
      setOpen(true);
      void queryClient.invalidateQueries({ queryKey: ["command-center", "api-keys"] });
    },
  });

  function resetDialog(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen) {
      setKeyName("");
      setRole("org_viewer");
      setOrgId("");
      setExpiresAt("");
      setGenerated(null);
      createMutation.reset();
    }
  }

  return (
    <>
      <PageHeader
        title="API Keys"
        description="Org-scoped credentials for the control plane API and in-cluster Operators"
        actions={canWriteKeys ? (
          <Dialog open={open} onOpenChange={resetDialog}>
            <DialogTrigger asChild>
              <Button size="sm"><Plus className="mr-1 h-4 w-4" />New API key</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>{generated ? "API key created" : "Create API key"}</DialogTitle></DialogHeader>
              {!generated ? (
                <form
                  className="space-y-3 text-sm"
                  onSubmit={(event) => {
                    event.preventDefault();
                    createMutation.mutate();
                  }}
                >
                  <div><Label>Name</Label><Input value={keyName} onChange={(event) => setKeyName(event.target.value)} placeholder="ci-deploy" required /></div>
                  <div>
                    <Label>Organization</Label>
                    <Select value={selectedOrg} onValueChange={setOrgId} disabled={availableOrgs.length <= 1}>
                      <SelectTrigger><SelectValue placeholder="Select org" /></SelectTrigger>
                      <SelectContent>
                        {availableOrgs.map((org) => <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Role</Label>
                    <Select value={role} onValueChange={(value) => setRole(value as ApiKeyRole)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="org_viewer">Org viewer</SelectItem>
                        <SelectItem value="org_admin">Org admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Expires</Label><Input value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} type="date" /></div>
                  {createMutation.isError && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">API key could not be created.</div>}
                  <DialogFooter>
                    <Button type="submit" disabled={!selectedOrg || !keyName || createMutation.isPending}>
                      {createMutation.isPending ? "Creating..." : "Create"}
                    </Button>
                  </DialogFooter>
                </form>
              ) : (
                <div className="space-y-3 text-sm">
                  <div className="rounded-md border border-warning/30 bg-warning/10 p-3 text-xs text-warning-foreground">
                    Copy this token now. For tenant isolation, the secret is shown only once and never stored in plaintext.
                  </div>
                  <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2 font-mono text-xs">
                    <span className="flex-1 break-all">{generated.token}</span>
                    <button type="button" onClick={() => void navigator.clipboard.writeText(generated.token)} className="text-muted-foreground hover:text-foreground"><Copy className="h-4 w-4" /></button>
                  </div>
                  <DialogFooter><Button variant="outline" onClick={() => resetDialog(false)}>Done</Button></DialogFooter>
                </div>
              )}
            </DialogContent>
          </Dialog>
        ) : undefined}
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
                    {canWriteKeys ? (
                      <>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs"
                          disabled={rotateMutation.isPending || k.status !== "active"}
                          onClick={() => rotateMutation.mutate({ org: k.org, id: k.id })}
                        >
                          Rotate
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs text-destructive"
                          disabled={revokeMutation.isPending || k.status !== "active"}
                          onClick={() => revokeMutation.mutate({ org: k.org, id: k.id })}
                        >
                          Revoke
                        </Button>
                      </>
                    ) : (
                      <span className="text-muted-foreground">Read only</span>
                    )}
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
