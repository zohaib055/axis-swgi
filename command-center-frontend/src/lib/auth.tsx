import * as React from "react";
import { ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export type Role = "platform_admin" | "platform_viewer" | "org_admin" | "org_viewer" | "operator";

export type Permission =
  | "org:read"
  | "org:write"
  | "cluster:read"
  | "cluster:write"
  | "api_key:write"
  | "user:write"
  | "settings:write"
  | "audit:read"
  | "billing:read"
  | "operator:read";

type User = {
  userId: string;
  email: string;
  name?: string;
  role: Role;
  orgId?: string | null;
};

type AuthContextValue = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (input: SignupInput) => Promise<void>;
  logout: () => void;
  can: (permission: Permission) => boolean;
};

const STORAGE_KEY = "swgi.command-center.session";
const API_BASE = (import.meta.env.VITE_SWGI_COMMAND_CENTER_PROXY ?? "/api/command-center").replace(/\/$/, "");

const ROLE_LABELS: Record<Role, string> = {
  platform_admin: "Platform admin",
  platform_viewer: "Platform viewer",
  org_admin: "Org admin",
  org_viewer: "Org viewer",
  operator: "Operator",
};

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  platform_admin: ["org:read", "org:write", "cluster:read", "cluster:write", "api_key:write", "user:write", "settings:write", "audit:read", "billing:read", "operator:read"],
  platform_viewer: ["org:read", "cluster:read", "audit:read", "billing:read", "operator:read"],
  org_admin: ["org:read", "cluster:read", "cluster:write", "api_key:write", "user:write", "audit:read", "billing:read", "operator:read"],
  org_viewer: ["org:read", "cluster:read", "audit:read", "billing:read", "operator:read"],
  operator: ["operator:read"],
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

type StoredSession = {
  expiresAt: string;
  user: User;
};

type LoginResponse = {
  access_token: string;
  expires_at: string;
  user: {
    user_id: string;
    email: string;
    display_name?: string | null;
    role: Role;
    org_id?: string | null;
  };
};

type ActionTokenResponse = {
  token: string;
  expires_at: string;
  delivery: string;
};

type SignupInput = {
  orgId: string;
  orgName: string;
  email: string;
  password: string;
  displayName?: string;
};

async function requestPasswordResetToken(email: string): Promise<ActionTokenResponse> {
  const response = await fetch(`${API_BASE}/v1/auth/password-reset`, {
    method: "POST",
    headers: { accept: "application/json", "content-type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error("Password reset failed");
  return response.json() as Promise<ActionTokenResponse>;
}

async function confirmPasswordResetToken(token: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE}/v1/auth/password-reset/confirm`, {
    method: "POST",
    headers: { accept: "application/json", "content-type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!response.ok) throw new Error("Password reset failed");
}

function mapUser(user: LoginResponse["user"]): User {
  return {
    userId: user.user_id,
    email: user.email,
    name: user.display_name ?? user.email,
    role: user.role,
    orgId: user.org_id ?? null,
  };
}

export function getStoredAuthSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

async function fetchMe(): Promise<User | null> {
  const response = await fetch(`${API_BASE}/v1/auth/me`, {
    headers: { accept: "application/json" },
    credentials: "same-origin",
  });
  if (!response.ok) return null;
  const user = (await response.json()) as LoginResponse["user"];
  return mapUser(user);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = React.useState(false);
  const [user, setUser] = React.useState<User | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    const session = getStoredAuthSession();
    if (session && new Date(session.expiresAt).getTime() > Date.now()) {
      setUser(session.user);
    }
    void fetchMe().then((me) => {
      if (cancelled) return;
      if (me) {
        setUser(me);
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
          expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
          user: me,
        }));
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
        setUser(null);
      }
      setReady(true);
    });
    if (session && new Date(session.expiresAt).getTime() <= Date.now()) {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    const session = getStoredAuthSession();
    if (session && user) {
      if (new Date(session.expiresAt).getTime() > Date.now()) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...session, user }));
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, [user]);

  const login = React.useCallback(async (email: string, password: string) => {
    const response = await fetch(`${API_BASE}/v1/auth/login`, {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
      },
      credentials: "same-origin",
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      throw new Error(response.status === 401 ? "Invalid email or password" : "Sign in failed");
    }
    const data = (await response.json()) as LoginResponse;
    const nextSession: StoredSession = {
      expiresAt: data.expires_at,
      user: mapUser(data.user),
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    setUser(nextSession.user);
  }, []);

  const signup = React.useCallback(async (input: SignupInput) => {
    const response = await fetch(`${API_BASE}/v1/auth/signup`, {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
      },
      credentials: "same-origin",
      body: JSON.stringify({
        org_id: input.orgId,
        org_name: input.orgName,
        email: input.email,
        password: input.password,
        display_name: input.displayName || input.email,
      }),
    });
    if (!response.ok) {
      throw new Error(response.status === 409 ? "Org or account already exists" : "Signup failed");
    }
    const data = (await response.json()) as LoginResponse;
    const nextSession: StoredSession = {
      expiresAt: data.expires_at,
      user: mapUser(data.user),
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    setUser(nextSession.user);
  }, []);

  const logout = React.useCallback(() => {
    const session = getStoredAuthSession();
    if (session) {
      void fetch(`${API_BASE}/v1/auth/logout`, {
        method: "POST",
        headers: {
          accept: "application/json",
        },
        credentials: "same-origin",
      });
    }
    window.localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  const can = React.useCallback(
    (permission: Permission) => Boolean(user && ROLE_PERMISSIONS[user.role].includes(permission)),
    [user],
  );

  return (
    <AuthContext.Provider value={{ user, ready, login, signup, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = React.useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}

export function roleLabel(role: Role) {
  return ROLE_LABELS[role];
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const auth = useAuth();

  if (!auth.ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        Loading Command Center...
      </div>
    );
  }

  if (!auth.user) {
    return <LoginScreen />;
  }

  return <>{children}</>;
}

export function RequirePermission({ permission, children }: { permission: Permission; children: React.ReactNode }) {
  const auth = useAuth();
  if (!auth.can(permission)) {
    return (
      <div className="flex min-h-[calc(100vh-3rem)] items-center justify-center bg-background px-4">
        <Card className="max-w-md p-5 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-muted text-muted-foreground">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <h1 className="text-base font-semibold text-foreground">Access restricted</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Your current role does not include permission to view this area.
          </p>
        </Card>
      </div>
    );
  }
  return <>{children}</>;
}

function LoginScreen() {
  const auth = useAuth();
  const [email, setEmail] = React.useState("admin@swgi.io");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [signupMode, setSignupMode] = React.useState(false);
  const [orgId, setOrgId] = React.useState("");
  const [orgName, setOrgName] = React.useState("");
  const [displayName, setDisplayName] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [resetMode, setResetMode] = React.useState(false);
  const [resetToken, setResetToken] = React.useState("");
  const [resetPassword, setResetPassword] = React.useState("");
  const [resetMessage, setResetMessage] = React.useState("");
  const [resetSubmitting, setResetSubmitting] = React.useState(false);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-foreground">SWGI Command Center</h1>
            <p className="text-xs text-muted-foreground">Secure admin access</p>
          </div>
        </div>
        {signupMode ? (
          <form
            className="space-y-3"
            onSubmit={async (event) => {
              event.preventDefault();
              setError("");
              setSubmitting(true);
              try {
                await auth.signup({ orgId, orgName, email, password, displayName });
              } catch (err) {
                setError(err instanceof Error ? err.message : "Signup failed");
              } finally {
                setSubmitting(false);
              }
            }}
          >
            <div className="space-y-1.5">
              <Label className="text-xs">Company</Label>
              <Input value={orgName} onChange={(event) => setOrgName(event.target.value)} className="h-9 text-sm" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Org ID</Label>
              <Input value={orgId} onChange={(event) => setOrgId(event.target.value)} className="h-9 font-mono text-sm" placeholder="acme" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="h-9 text-sm" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Work email</Label>
              <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="h-9 text-sm" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Password</Label>
              <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" className="h-9 text-sm" />
            </div>
            {error && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}
            <Button type="submit" className="w-full" disabled={submitting || !orgId || !orgName || !email || password.length < 12}>
              {submitting ? "Creating account..." : "Create account"}
            </Button>
            <Button type="button" variant="ghost" className="w-full" onClick={() => { setSignupMode(false); setError(""); }}>
              Back to sign in
            </Button>
          </form>
        ) : resetMode ? (
          <form
            className="space-y-3"
            onSubmit={async (event) => {
              event.preventDefault();
              setResetMessage("");
              setError("");
              setResetSubmitting(true);
              try {
                if (!resetToken) {
                  const result = await requestPasswordResetToken(email);
                  setResetToken(result.token);
                  setResetMessage(result.token ? "Reset token generated. Paste a new password below." : "If the account exists, reset instructions are available.");
                } else {
                  await confirmPasswordResetToken(resetToken, resetPassword);
                  setResetMessage("Password updated. Sign in with the new password.");
                  setResetToken("");
                  setResetPassword("");
                  setResetMode(false);
                }
              } catch (err) {
                setError(err instanceof Error ? err.message : "Password reset failed");
              } finally {
                setResetSubmitting(false);
              }
            }}
          >
            <div className="space-y-1.5">
              <Label className="text-xs">Email</Label>
              <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="h-9 text-sm" />
            </div>
            {resetToken && (
              <>
                <div className="space-y-1.5">
                  <Label className="text-xs">Reset token</Label>
                  <Input value={resetToken} onChange={(event) => setResetToken(event.target.value)} className="h-9 font-mono text-xs" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">New password</Label>
                  <Input value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} type="password" className="h-9 text-sm" />
                </div>
              </>
            )}
            {resetMessage && <div className="rounded-md border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">{resetMessage}</div>}
            {error && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}
            <Button type="submit" className="w-full" disabled={resetSubmitting || !email || (Boolean(resetToken) && resetPassword.length < 12)}>
              {resetSubmitting ? "Working..." : resetToken ? "Update password" : "Generate reset token"}
            </Button>
            <Button type="button" variant="ghost" className="w-full" onClick={() => { setResetMode(false); setError(""); }}>
              Back to sign in
            </Button>
          </form>
        ) : (
        <form
          className="space-y-3"
          onSubmit={async (event) => {
            event.preventDefault();
            setError("");
            setSubmitting(true);
            try {
              await auth.login(email, password);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Sign in failed");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <div className="space-y-1.5">
            <Label className="text-xs">Email</Label>
            <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Password</Label>
            <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" className="h-9 text-sm" />
          </div>
          {error && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
          <Button type="button" variant="ghost" className="w-full" onClick={() => { setResetMode(true); setError(""); }}>
            Forgot password
          </Button>
          <Button type="button" variant="outline" className="w-full" onClick={() => { setSignupMode(true); setError(""); }}>
            Create customer account
          </Button>
        </form>
        )}
      </Card>
    </div>
  );
}
