import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, UserPlus } from "lucide-react";
import { RequirePermission, useAuth } from "@/lib/auth";
import { changeUserPassword, createUser, updateUserStatus, useOrganizations, useUsers, type UserRole } from "@/lib/command-center-api";

export const Route = createFileRoute("/users")({
  head: () => ({ meta: [{ title: "Users — SWGI" }] }),
  component: Users,
});

function Users() {
  return (
    <RequirePermission permission="user:write">
      <UsersContent />
    </RequirePermission>
  );
}

function UsersContent() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const { data: users } = useUsers();
  const { data: orgs } = useOrganizations();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>(auth.user?.role === "platform_admin" ? "org_admin" : "org_viewer");
  const [orgId, setOrgId] = useState("");
  const [resetUser, setResetUser] = useState<{ id: string; email: string } | null>(null);
  const [resetPassword, setResetPassword] = useState("");
  const visibleOrgs = auth.user?.orgId ? orgs.filter((org) => org.id === auth.user?.orgId) : orgs;
  const selectedOrg = orgId || visibleOrgs[0]?.id || auth.user?.orgId || "";
  const roleOptions: { value: UserRole; label: string }[] = auth.user?.role === "platform_admin"
    ? [
        { value: "platform_admin", label: "Platform admin" },
        { value: "platform_viewer", label: "Platform viewer" },
        { value: "org_admin", label: "Org admin" },
        { value: "org_viewer", label: "Org viewer" },
      ]
    : [
        { value: "org_admin", label: "Org admin" },
        { value: "org_viewer", label: "Org viewer" },
      ];
  const requiresOrg = role.startsWith("org_");
  const createMutation = useMutation({
    mutationFn: () => createUser({
      email,
      password,
      displayName,
      role,
      orgId: requiresOrg ? selectedOrg : null,
    }),
    onSuccess: () => {
      setOpen(false);
      resetCreateForm();
      void queryClient.invalidateQueries({ queryKey: ["command-center", "users"] });
    },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "active" | "disabled" }) => updateUserStatus(id, status),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["command-center", "users"] }),
  });
  const passwordMutation = useMutation({
    mutationFn: () => resetUser ? changeUserPassword(resetUser.id, resetPassword) : Promise.resolve({ status: "skipped" }),
    onSuccess: () => {
      setResetUser(null);
      setResetPassword("");
      void queryClient.invalidateQueries({ queryKey: ["command-center", "users"] });
    },
  });

  function resetCreateForm() {
    setEmail("");
    setDisplayName("");
    setPassword("");
    setRole(auth.user?.role === "platform_admin" ? "org_admin" : "org_viewer");
    setOrgId("");
    createMutation.reset();
  }

  return (
    <>
      <PageHeader
        title="Users"
        description="Customer and platform admin access backed by Command Center Postgres"
        actions={
          <Dialog open={open} onOpenChange={(nextOpen) => { setOpen(nextOpen); if (!nextOpen) resetCreateForm(); }}>
            <DialogTrigger asChild>
              <Button size="sm"><Plus className="mr-1 h-4 w-4" />New user</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create user</DialogTitle></DialogHeader>
              <form
                className="space-y-3 text-sm"
                onSubmit={(event) => {
                  event.preventDefault();
                  createMutation.mutate();
                }}
              >
                <div><Label>Email</Label><Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></div>
                <div><Label>Name</Label><Input value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></div>
                <div>
                  <Label>Role</Label>
                  <Select value={role} onValueChange={(value) => setRole(value as UserRole)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {roleOptions.map((item) => <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                {requiresOrg && (
                  <div>
                    <Label>Organization</Label>
                    <Select value={selectedOrg} onValueChange={setOrgId} disabled={visibleOrgs.length <= 1}>
                      <SelectTrigger><SelectValue placeholder="Select org" /></SelectTrigger>
                      <SelectContent>
                        {visibleOrgs.map((org) => <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <div><Label>Temporary password</Label><Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required minLength={12} /></div>
                {createMutation.isError && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">User could not be created.</div>}
                <DialogFooter><Button type="submit" disabled={createMutation.isPending || !email || !password || (requiresOrg && !selectedOrg)}>{createMutation.isPending ? "Creating..." : "Create"}</Button></DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />
      <div className="space-y-4 p-6">
        <Card className="p-0">
          <table className="w-full text-xs">
            <thead className="bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr><th className="px-4 py-2 text-left">User</th><th className="px-4 py-2 text-left">Org</th><th className="px-4 py-2 text-left">Role</th><th className="px-4 py-2 text-left">Last login</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-right">Actions</th></tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-4 py-2"><div className="font-medium">{user.name}</div><div className="text-muted-foreground">{user.email}</div></td>
                  <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">{user.org || "platform"}</td>
                  <td className="px-4 py-2"><StatusBadge variant={user.role.includes("admin") ? "info" : "muted"}>{user.role}</StatusBadge></td>
                  <td className="px-4 py-2 tabular-nums text-muted-foreground">{user.lastLogin}</td>
                  <td className="px-4 py-2"><StatusBadge dot variant={user.status === "active" ? "success" : "destructive"}>{user.status}</StatusBadge></td>
                  <td className="px-4 py-2 text-right">
                    <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setResetUser({ id: user.id, email: user.email })}>Password</Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className={user.status === "active" ? "h-7 text-xs text-destructive" : "h-7 text-xs"}
                      disabled={statusMutation.isPending || user.id === auth.user?.userId}
                      onClick={() => statusMutation.mutate({ id: user.id, status: user.status === "active" ? "disabled" : "active" })}
                    >
                      {user.status === "active" ? "Disable" : "Activate"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
      <Dialog open={Boolean(resetUser)} onOpenChange={(nextOpen) => { if (!nextOpen) { setResetUser(null); setResetPassword(""); passwordMutation.reset(); } }}>
        <DialogContent>
          <DialogHeader><DialogTitle>Reset password</DialogTitle></DialogHeader>
          <form
            className="space-y-3 text-sm"
            onSubmit={(event) => {
              event.preventDefault();
              passwordMutation.mutate();
            }}
          >
            <div className="rounded-md border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
              <UserPlus className="mr-2 inline h-3.5 w-3.5" />
              {resetUser?.email}
            </div>
            <div><Label>New password</Label><Input value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} type="password" required minLength={12} /></div>
            {passwordMutation.isError && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">Password could not be updated.</div>}
            <DialogFooter><Button type="submit" disabled={passwordMutation.isPending || resetPassword.length < 12}>{passwordMutation.isPending ? "Updating..." : "Update password"}</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
