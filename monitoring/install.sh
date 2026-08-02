#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
CHART_VERSION="87.18.0"
RELEASE_NAME="monitoring"
MONITORING_NAMESPACE="monitoring"

log() {
  printf '%s\n' "[monitoring] $*"
}

for required_command in helm kubectl; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "${required_command}" >&2
    exit 1
  fi
done

log "Configuring prometheus-community Helm repository"
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts \
  --force-update
helm repo update prometheus-community

log "Installing or upgrading kube-prometheus-stack ${CHART_VERSION}"
helm upgrade --install "${RELEASE_NAME}" prometheus-community/kube-prometheus-stack \
  --version "${CHART_VERSION}" \
  --namespace "${MONITORING_NAMESPACE}" \
  --create-namespace \
  --values "${REPOSITORY_ROOT}/monitoring/values.yaml" \
  --wait \
  --timeout 10m

log "Applying ShelfSense ServiceMonitor and alert rules"
kubectl apply -f "${REPOSITORY_ROOT}/monitoring/servicemonitors/shelfsense-backend.yaml"
kubectl apply -f "${REPOSITORY_ROOT}/monitoring/rules/shelfsense-alerts.yaml"

log "Creating or updating the ShelfSense Grafana dashboard"
kubectl create configmap shelfsense-grafana-dashboard \
  --namespace "${MONITORING_NAMESPACE}" \
  --from-file="shelfsense-overview.json=${REPOSITORY_ROOT}/monitoring/dashboards/shelfsense-overview.json" \
  --dry-run=client \
  --output yaml | kubectl apply -f -
kubectl label configmap shelfsense-grafana-dashboard \
  --namespace "${MONITORING_NAMESPACE}" \
  grafana_dashboard=1 \
  --overwrite

log "Monitoring installation is ready; Grafana remains internal-only"
