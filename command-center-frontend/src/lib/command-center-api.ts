import { useQuery, type DefinedUseQueryResult } from "@tanstack/react-query";
import { getStoredAuthSession } from "@/lib/auth";

const API_BASE = (import.meta.env.VITE_SWGI_COMMAND_CENTER_PROXY ?? "/api/command-center").replace(/\/$/, "");

export type Decision = "ALLOW" | "DENY" | "MODIFY";
export type Runtime = "Kubernetes" | "OpenShift" | "GKE" | "EKS" | "AKS" | "on-prem";
export type ClusterStatus = "healthy" | "degraded" | "disconnected";
export type ExecStatus = "pending" | "running" | "succeeded" | "failed" | "rejected";
export type ApiKeyRole = "org_admin" | "org_viewer" | "operator";

type OrgResponse = {
  org_id: string;
  display_name?: string | null;
  status: string;
  plan_code: string;
};

type ClusterResponse = {
  cluster_id: string;
  org_id: string;
  runtime: string;
  display_name?: string | null;
  status: string;
  health?: string | null;
  operator_version?: string | null;
  heartbeat_namespace?: string | null;
  last_seen_at?: string | null;
  last_heartbeat_at?: string | null;
};

type UsageResponse = {
  total_executions: number;
  allowed_executions: number;
  denied_attempts: number;
  modified_executions: number;
  cluster_count: number;
  namespace_count: number;
};

type ReceiptResponse = {
  receipt_id: string;
  org_id: string;
  cluster_id: string;
  namespace: string;
  workload_id: string;
  decision: Decision;
  policy_id: string;
  payload_hash: string;
  integrity_classification?: string | null;
  created_at: string;
  expires_at: string;
};

type ReceiptListResponse = {
  count: number;
  items: ReceiptResponse[];
};

type OperatorEventResponse = {
  id?: number | string;
  receipt_id: string;
  org_id?: string;
  cluster_id: string;
  namespace: string;
  workload_id: string;
  enforcement_status: string;
  error_code?: string | null;
  error_summary?: string | null;
  created_at?: string;
};

type AuditLogResponse = {
  audit_id: number | string;
  created_at: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  outcome: string;
  request_id?: string | null;
};

type PolicyResponse = {
  policy_id: string;
  org_id: string;
  version?: string | null;
  active: boolean;
};

type ApiKeyResponse = {
  api_key_id: string;
  org_id?: string | null;
  cluster_id?: string | null;
  key_name: string;
  role: ApiKeyRole;
  status: string;
  created_at: string;
  expires_at?: string | null;
  last_used_at?: string | null;
  revoked_at?: string | null;
};

type ApiKeyCreateResponse = {
  api_key: ApiKeyResponse;
  token: string;
};

type UserResponse = {
  user_id: string;
  email: string;
  display_name?: string | null;
  role: string;
  org_id?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
  last_login_at?: string | null;
};

export type UserRole = "platform_admin" | "platform_viewer" | "org_admin" | "org_viewer" | "operator";

export type CreateApiKeyInput = {
  orgId: string;
  keyName: string;
  role: ApiKeyRole;
  expiresAt?: string;
};

export type CreateUserInput = {
  email: string;
  password: string;
  displayName?: string;
  role: UserRole;
  orgId?: string | null;
};

const EMPTY_USAGE = {
  totalExecutions: 0,
  allow: 0,
  deny: 0,
  modify: 0,
  activeClusters: 0,
  degradedOperators: 0,
  disconnectedOperators: 0,
  monthlyUsage: 0,
  planLimit: 0,
};

async function commandCenterFetch<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const session = getStoredAuthSession();
  const headers = new Headers(init.headers);
  headers.set("accept", "application/json");
  if (init.json !== undefined) {
    headers.set("content-type", "application/json");
  }
  if (session?.accessToken) {
    headers.set("authorization", `Bearer ${session.accessToken}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    body: init.json === undefined ? init.body : JSON.stringify(init.json),
  });
  if (!response.ok) {
    throw new Error(`Command Center API ${response.status}: ${path}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

function useCommandCenterQuery<T>(
  key: readonly unknown[],
  queryFn: () => Promise<T>,
  initialData: T,
): DefinedUseQueryResult<T, Error> {
  return useQuery({
    queryKey: ["command-center", ...key],
    queryFn,
    initialData,
    retry: 1,
    staleTime: 15_000,
  }) as DefinedUseQueryResult<T, Error>;
}

function currentUserScope() {
  return getStoredAuthSession()?.user ?? null;
}

async function fetchVisibleOrganizations(): Promise<OrgResponse[]> {
  const user = currentUserScope();
  if (user?.orgId && !user.role.startsWith("platform_")) {
    return [await commandCenterFetch<OrgResponse>(`/v1/orgs/${user.orgId}`)];
  }
  return commandCenterFetch<OrgResponse[]>("/v1/orgs");
}

export function useOrganizations() {
  return useCommandCenterQuery(["orgs"], async () => {
    const rows = await fetchVisibleOrganizations();
    return rows.map((org) => ({
      id: org.org_id,
      name: org.display_name || org.org_id,
      plan: title(org.plan_code),
      status: org.status,
      clusters: 0,
      monthlyExecutions: 0,
    }));
  }, []);
}

export function useClusters() {
  return useCommandCenterQuery(["clusters"], async () => {
    const rows = await commandCenterFetch<ClusterResponse[]>("/v1/clusters");
    return rows.map((cluster) => ({
      id: cluster.cluster_id,
      name: cluster.display_name || cluster.cluster_id,
      org: cluster.org_id,
      runtime: mapRuntime(cluster.runtime),
      status: mapClusterStatus(cluster.health || cluster.status),
      lastHeartbeat: relative(cluster.last_heartbeat_at || cluster.last_seen_at),
      operatorVersion: cluster.operator_version || "unknown",
      namespaces: 0,
    }));
  }, []);
}

export function useReceipts() {
  return useCommandCenterQuery(["receipts"], async () => {
    const response = await commandCenterFetch<ReceiptListResponse>("/v1/receipts?limit=100");
    return response.items.map((receipt) => ({
      id: receipt.receipt_id,
      org: receipt.org_id,
      cluster: receipt.cluster_id,
      namespace: receipt.namespace,
      workload: receipt.workload_id,
      decision: receipt.decision,
      policy: receipt.policy_id,
      payloadHash: receipt.payload_hash,
      signatureStatus: "verified",
      expiresAt: relative(receipt.expires_at),
      enforcement: receipt.decision === "DENY" ? "blocked" : "pending",
      createdAt: relative(receipt.created_at),
    }));
  }, []);
}

export function useUsage() {
  return useCommandCenterQuery(["usage"], async () => {
    const usage = await commandCenterFetch<UsageResponse>("/v1/usage");
    return {
      totalExecutions: usage.total_executions,
      allow: usage.allowed_executions,
      deny: usage.denied_attempts,
      modify: usage.modified_executions,
      activeClusters: usage.cluster_count,
      degradedOperators: 0,
      disconnectedOperators: 0,
      monthlyUsage: usage.total_executions,
      planLimit: Math.max(usage.total_executions, 1),
    };
  }, EMPTY_USAGE);
}

export function useOperatorEvents() {
  return useCommandCenterQuery(["operator-events"], async () => {
    const rows = await commandCenterFetch<OperatorEventResponse[]>("/v1/operator-events?limit=100");
    return rows.map((event, index) => ({
      id: String(event.id ?? `${event.receipt_id}_${index}`),
      receipt: event.receipt_id,
      cluster: event.cluster_id,
      namespace: event.namespace,
      workload: event.workload_id,
      status: mapOperatorStatus(event.enforcement_status),
      message: event.error_summary || event.error_code || event.enforcement_status,
      at: relative(event.created_at),
    }));
  }, []);
}

export function useAuditLogs() {
  return useCommandCenterQuery(["audit-logs"], async () => {
    const rows = await commandCenterFetch<AuditLogResponse[]>("/v1/audit-logs?limit=100");
    return rows.map((log) => ({
      id: String(log.audit_id),
      at: formatDate(log.created_at),
      actor: log.actor_role,
      role: log.actor_role,
      action: log.action,
      resource: log.resource_id || log.resource_type,
      outcome: log.outcome,
      requestId: log.request_id || "",
    }));
  }, []);
}

export function usePolicies() {
  return useCommandCenterQuery(["policies"], async () => {
    const rows = await commandCenterFetch<PolicyResponse[]>("/v1/policies");
    return rows.map((policy) => ({
      id: policy.policy_id,
      name: policy.policy_id,
      scope: policy.org_id,
      attached: 0,
      version: policy.version || "1",
      active: policy.active,
    }));
  }, []);
}

export function useExecutions() {
  const receiptsQuery = useReceipts();
  return {
    ...receiptsQuery,
    data: receiptsQuery.data.map((receipt) => ({
      id: receipt.id,
      receiptId: receipt.id,
      cluster: receipt.cluster,
      namespace: receipt.namespace,
      workload: receipt.workload,
      action: "governed execution",
      payloadHash: receipt.payloadHash,
      status: (receipt.enforcement === "blocked" ? "rejected" : "pending") as ExecStatus,
      createdAt: receipt.createdAt,
      updatedAt: receipt.createdAt,
    })),
  };
}

export function useApiKeys() {
  return useCommandCenterQuery(["api-keys"], async () => {
    const user = currentUserScope();
    const orgIds = user?.orgId && !user.role.startsWith("platform_")
      ? [user.orgId]
      : (await fetchVisibleOrganizations()).map((org) => org.org_id);
    const rows = (await Promise.all(
      orgIds.map((orgId) => commandCenterFetch<ApiKeyResponse[]>(`/v1/orgs/${orgId}/api-keys`)),
    )).flat();
    return rows.map((key) => ({
      id: key.api_key_id,
      org: key.org_id || "",
      name: key.key_name,
      role: key.role,
      created: formatDate(key.created_at),
      lastUsed: relative(key.last_used_at),
      expires: key.expires_at ? formatDate(key.expires_at) : "never",
      status: key.status,
    }));
  }, []);
}

export function useUsers() {
  return useCommandCenterQuery(["users"], async () => {
    const rows = await commandCenterFetch<UserResponse[]>("/v1/users");
    return rows.map((user) => ({
      id: user.user_id,
      email: user.email,
      name: user.display_name || user.email,
      role: user.role as UserRole,
      org: user.org_id || "",
      status: user.status,
      created: formatDate(user.created_at),
      lastLogin: relative(user.last_login_at),
    }));
  }, []);
}

export async function createApiKey(input: CreateApiKeyInput) {
  const response = await commandCenterFetch<ApiKeyCreateResponse>(`/v1/orgs/${input.orgId}/api-keys`, {
    method: "POST",
    json: {
      key_name: input.keyName,
      role: input.role,
      expires_at: input.expiresAt ? new Date(input.expiresAt).toISOString() : null,
    },
  });
  return {
    id: response.api_key.api_key_id,
    org: response.api_key.org_id || "",
    name: response.api_key.key_name,
    role: response.api_key.role,
    token: response.token,
  };
}

export async function revokeApiKey(orgId: string, apiKeyId: string) {
  return commandCenterFetch<{ status: string }>(`/v1/orgs/${orgId}/api-keys/${apiKeyId}`, {
    method: "DELETE",
  });
}

export async function rotateApiKey(orgId: string, apiKeyId: string) {
  const response = await commandCenterFetch<ApiKeyCreateResponse>(`/v1/orgs/${orgId}/api-keys/${apiKeyId}/rotate`, {
    method: "POST",
  });
  return {
    id: response.api_key.api_key_id,
    org: response.api_key.org_id || "",
    name: response.api_key.key_name,
    role: response.api_key.role,
    token: response.token,
  };
}

export async function createUser(input: CreateUserInput) {
  return commandCenterFetch<UserResponse>("/v1/users", {
    method: "POST",
    json: {
      email: input.email,
      password: input.password,
      display_name: input.displayName || null,
      role: input.role,
      org_id: input.orgId || null,
    },
  });
}

export async function updateUserStatus(userId: string, status: "active" | "disabled") {
  return commandCenterFetch<UserResponse>(`/v1/users/${userId}`, {
    method: "PATCH",
    json: { status },
  });
}

export async function changeUserPassword(userId: string, newPassword: string) {
  return commandCenterFetch<{ status: string }>(`/v1/users/${userId}/password`, {
    method: "POST",
    json: { new_password: newPassword },
  });
}

function mapRuntime(runtime: string): Runtime {
  const normalized = runtime.toLowerCase();
  if (normalized === "openshift") return "OpenShift";
  if (normalized === "gke") return "GKE";
  if (normalized === "eks") return "EKS";
  if (normalized === "aks") return "AKS";
  if (normalized.includes("prem")) return "on-prem";
  return "Kubernetes";
}

function mapClusterStatus(status: string): ClusterStatus {
  const normalized = status.toLowerCase();
  if (normalized === "active" || normalized === "healthy") return "healthy";
  if (normalized === "degraded" || normalized === "pending") return "degraded";
  return "disconnected";
}

function mapOperatorStatus(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === "succeeded") return "applied";
  return normalized;
}

function title(value: string): string {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function relative(value?: string | null): string {
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const delta = date.getTime() - Date.now();
  const abs = Math.abs(delta);
  const suffix = delta >= 0 ? "from now" : "ago";
  const minutes = Math.round(abs / 60_000);
  if (minutes < 1) return delta >= 0 ? "now" : "just now";
  if (minutes < 60) return `${minutes}m ${suffix}`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ${suffix}`;
  return formatDate(value);
}

function formatDate(value?: string | null): string {
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}
