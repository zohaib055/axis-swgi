// Mock data for SWGI Command Center. Replace with API calls later.

export type Decision = "ALLOW" | "DENY" | "MODIFY";
export type Runtime = "Kubernetes" | "OpenShift" | "GKE" | "EKS" | "AKS" | "on-prem";
export type ClusterStatus = "healthy" | "degraded" | "disconnected";
export type ExecStatus = "pending" | "running" | "succeeded" | "failed" | "rejected";
export type ApiKeyRole = "org_admin" | "org_viewer" | "operator";

export const orgs = [
  { id: "org_acme", name: "Acme Corp", plan: "Enterprise", status: "active", clusters: 7, monthlyExecutions: 184230 },
  { id: "org_globex", name: "Globex Industries", plan: "Growth", status: "active", clusters: 3, monthlyExecutions: 42100 },
  { id: "org_initech", name: "Initech", plan: "Starter", status: "trial", clusters: 1, monthlyExecutions: 1820 },
  { id: "org_umbrella", name: "Umbrella Systems", plan: "Enterprise", status: "active", clusters: 12, monthlyExecutions: 421900 },
  { id: "org_hooli", name: "Hooli", plan: "Growth", status: "suspended", clusters: 2, monthlyExecutions: 0 },
];

export const clusters = [
  { id: "clu_prod_us_east", name: "prod-us-east", org: "org_acme", runtime: "EKS" as Runtime, status: "healthy" as ClusterStatus, lastHeartbeat: "12s ago", operatorVersion: "v1.8.3", namespaces: 24 },
  { id: "clu_prod_eu", name: "prod-eu-west", org: "org_acme", runtime: "GKE" as Runtime, status: "healthy" as ClusterStatus, lastHeartbeat: "8s ago", operatorVersion: "v1.8.3", namespaces: 18 },
  { id: "clu_stg", name: "staging", org: "org_acme", runtime: "Kubernetes" as Runtime, status: "degraded" as ClusterStatus, lastHeartbeat: "2m ago", operatorVersion: "v1.7.9", namespaces: 9 },
  { id: "clu_ocp", name: "ocp-prod", org: "org_umbrella", runtime: "OpenShift" as Runtime, status: "healthy" as ClusterStatus, lastHeartbeat: "5s ago", operatorVersion: "v1.8.3", namespaces: 41 },
  { id: "clu_aks", name: "azure-prod", org: "org_globex", runtime: "AKS" as Runtime, status: "disconnected" as ClusterStatus, lastHeartbeat: "47m ago", operatorVersion: "v1.6.2", namespaces: 6 },
  { id: "clu_onprem", name: "dc-onprem-1", org: "org_umbrella", runtime: "on-prem" as Runtime, status: "healthy" as ClusterStatus, lastHeartbeat: "20s ago", operatorVersion: "v1.8.3", namespaces: 14 },
];

export const receipts = Array.from({ length: 24 }).map((_, i) => {
  const decisions: Decision[] = ["ALLOW", "ALLOW", "ALLOW", "MODIFY", "DENY"];
  const decision = decisions[i % decisions.length];
  return {
    id: `rcpt_${(1000 + i).toString(36)}`,
    org: orgs[i % orgs.length].id,
    cluster: clusters[i % clusters.length].id,
    namespace: ["payments", "platform", "data", "ml", "infra"][i % 5],
    workload: ["api-gateway", "ingestor", "trainer", "scheduler", "billing"][i % 5],
    decision,
    policy: ["pol-prod-baseline", "pol-pci-dss", "pol-ml-quota", "pol-deny-privileged"][i % 4],
    payloadHash: `sha256:${Math.random().toString(16).slice(2, 18)}…`,
    signatureStatus: "verified",
    expiresAt: `in ${2 + (i % 9)}m`,
    enforcement: decision === "DENY" ? "blocked" : "applied",
    createdAt: `${1 + i}m ago`,
  };
});

export const executions = Array.from({ length: 30 }).map((_, i) => {
  const statuses: ExecStatus[] = ["pending", "running", "succeeded", "failed", "rejected"];
  const status = statuses[i % statuses.length];
  return {
    id: `exec_${(2000 + i).toString(36)}`,
    receiptId: receipts[i % receipts.length].id,
    cluster: clusters[i % clusters.length].id,
    namespace: receipts[i % receipts.length].namespace,
    workload: receipts[i % receipts.length].workload,
    action: ["apply", "scale", "rollout", "delete", "patch"][i % 5],
    payloadHash: receipts[i % receipts.length].payloadHash,
    status,
    createdAt: `${2 + i}m ago`,
    updatedAt: `${1 + (i % 5)}m ago`,
  };
});

export const apiKeys = [
  { id: "key_a1", org: "org_acme", name: "ci-deploy", role: "org_admin" as ApiKeyRole, created: "2025-02-11", lastUsed: "3m ago", expires: "2026-02-11", status: "active" },
  { id: "key_a2", org: "org_acme", name: "operator-prod-us-east", role: "operator" as ApiKeyRole, created: "2025-01-04", lastUsed: "12s ago", expires: "never", status: "active" },
  { id: "key_a3", org: "org_globex", name: "readonly-dashboard", role: "org_viewer" as ApiKeyRole, created: "2024-11-22", lastUsed: "2d ago", expires: "2025-11-22", status: "active" },
  { id: "key_a4", org: "org_umbrella", name: "operator-ocp", role: "operator" as ApiKeyRole, created: "2024-09-08", lastUsed: "5s ago", expires: "never", status: "active" },
  { id: "key_a5", org: "org_initech", name: "trial-key", role: "org_admin" as ApiKeyRole, created: "2025-04-30", lastUsed: "—", expires: "2025-05-30", status: "revoked" },
];

export const operatorEvents = Array.from({ length: 20 }).map((_, i) => ({
  id: `evt_${i}`,
  receipt: receipts[i % receipts.length].id,
  cluster: clusters[i % clusters.length].id,
  namespace: receipts[i % receipts.length].namespace,
  workload: receipts[i % receipts.length].workload,
  status: ["applied", "applied", "applied", "rejected", "failed"][i % 5],
  message: ["enforced ok", "enforced ok", "enforced ok", "policy violation", "operator timeout"][i % 5],
  at: `${i + 1}m ago`,
}));

export const auditLogs = Array.from({ length: 25 }).map((_, i) => ({
  id: `audit_${i}`,
  at: `2025-05-0${(i % 7) + 1} 1${i % 9}:${(i * 7) % 60}`.padEnd(19, "0"),
  actor: ["alice@acme.io", "bob@globex.com", "operator-prod", "ci-runner"][i % 4],
  role: ["org_admin", "org_viewer", "operator", "org_admin"][i % 4],
  action: ["api_key.create", "cluster.register", "receipt.issue", "execution.update", "org.update"][i % 5],
  resource: ["org_acme", "clu_prod_us_east", "rcpt_3l9", "exec_4ka", "org_globex"][i % 5],
  outcome: ["success", "success", "success", "denied", "success"][i % 5],
  requestId: `req_${(1000 + i).toString(16)}`,
}));

export const policies = [
  { id: "pol-prod-baseline", name: "Production Baseline", scope: "org", attached: 7, version: "1.4" },
  { id: "pol-pci-dss", name: "PCI DSS Controls", scope: "namespace:payments", attached: 3, version: "2.1" },
  { id: "pol-ml-quota", name: "ML Workload Quotas", scope: "namespace:ml", attached: 2, version: "1.0" },
  { id: "pol-deny-privileged", name: "Deny Privileged Pods", scope: "cluster", attached: 11, version: "3.0" },
];

export const dashboardStats = {
  totalExecutions: 184230,
  allow: 168901,
  deny: 9842,
  modify: 5487,
  activeClusters: 23,
  degradedOperators: 2,
  disconnectedOperators: 1,
  monthlyUsage: 184230,
  planLimit: 250000,
};
