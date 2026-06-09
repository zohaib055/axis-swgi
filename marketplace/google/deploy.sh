#!/usr/bin/env bash
set -euo pipefail

: "${APP_NAME:?APP_NAME is required}"
: "${NAMESPACE:?NAMESPACE is required}"
: "${COMMAND_CENTER_URL:?COMMAND_CENTER_URL is required}"
: "${ORG_ID:?ORG_ID is required}"
: "${CLUSTER_ID:?CLUSTER_ID is required}"
: "${OPERATOR_TOKEN:?OPERATOR_TOKEN is required}"
: "${PUBLIC_SIGNING_KEY_PEM:?PUBLIC_SIGNING_KEY_PEM is required}"
: "${OPERATOR_IMAGE:?OPERATOR_IMAGE is required}"
: "${ENFORCEMENT_IMAGE:?ENFORCEMENT_IMAGE is required}"

export RECEIPT_ARCHIVE_BUCKET="${RECEIPT_ARCHIVE_BUCKET:-}"
export ENABLE_CLOUD_LOGGING="${ENABLE_CLOUD_LOGGING:-true}"
export ENABLE_CLOUD_MONITORING="${ENABLE_CLOUD_MONITORING:-true}"

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

for template in /data/templates/application.yaml /data/templates/operator.yaml; do
  envsubst < "${template}" | kubectl apply -f -
done
