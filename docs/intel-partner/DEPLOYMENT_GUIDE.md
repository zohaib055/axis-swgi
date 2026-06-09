# Intel Partner Deployment Guide

This guide describes how SWGI should be deployed for customers running on
Intel-based Kubernetes infrastructure.

## Supported Customer Environments

- Kubernetes clusters on Intel Xeon worker nodes.
- Red Hat OpenShift on Intel infrastructure.
- GKE / GKE Enterprise node pools backed by Intel machine families.
- Private cloud and edge Kubernetes clusters using Intel platforms.
- Optional Intel TDX capable environments for confidential workloads.

## Base Deployment

1. Customer creates an organization in SWGI Command Center.
2. Customer registers an Intel-based cluster.
3. Command Center generates Operator install config:
   - `COMMAND_CENTER_URL`
   - `ORG_ID`
   - `CLUSTER_ID`
   - `OPERATOR_TOKEN`
   - `PUBLIC_SIGNING_KEY_PEM`
4. Customer deploys SWGI Operator and enforcement pods.
5. Operator heartbeats to Command Center.
6. Customer validates receipts, executions, audit logs, and operator events.

## Intel TDX Optional Deployment

For confidential workload customers:

1. Confirm Intel TDX capable hardware and firmware.
2. Configure a confidential VM or confidential container runtime supported by
   the customer's Kubernetes platform.
3. Configure attestation provider and verifier.
4. Expose attestation verification result to SWGI policy evaluation.
5. Add policy rules requiring verified confidential runtime for selected
   workloads.
6. Confirm Trust Receipts include confidential runtime metadata or references.
7. Confirm enforcement rejects protected workloads when attestation is missing
   or invalid.

## Production Controls

- Enable JSON logs and central log collection.
- Enable metrics and readiness checks.
- Keep customer payloads outside Command Center.
- Store Operator tokens in Kubernetes Secrets.
- Keep signing keys and Command Center secrets in a production secrets manager.
- Use customer-owned retention for receipt archives when required.
- Record node pool, runtime class, workload identity, and attestation reference
  when confidential computing controls are enabled.

## Demo Flow For Intel Conversations

Use this flow for Intel partner demos and enterprise customer calls:

1. Show self-serve customer signup and org admin login.
2. Register an Intel-based Kubernetes cluster.
3. Show Operator heartbeat and cluster health.
4. Submit a governed workload intent.
5. Show Trust Receipt with policy, workload, cluster, and execution metadata.
6. Show audit log and operator event.
7. For TDX demos, show policy allowing only verified confidential workloads.
