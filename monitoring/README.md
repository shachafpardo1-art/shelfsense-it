# ShelfSense monitoring

## Architecture

Monitoring is a separate Helm release from the ShelfSense application. The `kube-prometheus-stack` release runs in the `monitoring` namespace, while its ServiceMonitor and PrometheusRule select the backend in the `shelfsense` namespace.

```text
Prometheus -> ServiceMonitor -> shelfsense-backend:8000/metrics
     |             (internal ClusterIP traffic only)
     +-> kube-state-metrics
     +-> node-exporter DaemonSet
     +-> alert rules -> Alertmanager

dashboard ConfigMap -> Grafana sidecar -> Grafana
```

Prometheus, Alertmanager, and Grafana use ephemeral storage. They do not use the PostgreSQL EBS volume. Grafana remains a `ClusterIP` Service and is accessed only with `kubectl port-forward`.

## Prerequisites

- A running K3s cluster with the ShelfSense release installed in `shelfsense`
- Helm 3 and `kubectl` configured for that cluster
- Kubernetes 1.25 or newer for kube-prometheus-stack `87.18.0`

## Install or upgrade

Use the repository-managed installer as the normal installation path:

```bash
./monitoring/install.sh
```

The script is idempotent: it adds or refreshes the Helm repository, installs or upgrades the monitoring release, applies the ServiceMonitor and PrometheusRule, and creates or updates the dashboard ConfigMap. It honors `KUBECONFIG` when that environment variable is set. It does not expose Grafana publicly.

## Manual installation reference

Use the following commands for troubleshooting or when running individual installation steps manually.

Add and refresh the chart repository:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update prometheus-community
```

Install or upgrade the separate monitoring release:

```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 87.18.0 \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/values.yaml
```

Apply application discovery and alerting resources after the chart CRDs are installed:

```bash
kubectl apply -f monitoring/servicemonitors/shelfsense-backend.yaml
kubectl apply -f monitoring/rules/shelfsense-alerts.yaml
```

Create or update the dashboard ConfigMap, then label it for the Grafana dashboard sidecar:

```bash
kubectl create configmap shelfsense-grafana-dashboard \
  --namespace monitoring \
  --from-file=shelfsense-overview.json=monitoring/dashboards/shelfsense-overview.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap shelfsense-grafana-dashboard \
  --namespace monitoring \
  grafana_dashboard=1 \
  --overwrite
```

## Access Grafana

Read the chart-generated admin password without storing it in Git:

```bash
kubectl get secret monitoring-grafana \
  --namespace monitoring \
  --output jsonpath='{.data.admin-password}' | base64 --decode
echo
```

Forward Grafana locally and open `http://127.0.0.1:3000`:

```bash
kubectl port-forward --namespace monitoring service/monitoring-grafana 3000:80
```

Log in as `admin` with the generated password. Grafana has no Ingress or public Service.

## Validate collection

Confirm the expected components. Node exporter should appear as a DaemonSet:

```bash
kubectl get pods,services,statefulsets,daemonsets --namespace monitoring
kubectl get servicemonitor --namespace shelfsense shelfsense-backend
kubectl get prometheusrule --namespace shelfsense shelfsense-alerts
```

Forward Prometheus locally:

```bash
kubectl port-forward --namespace monitoring service/monitoring-kube-prometheus-prometheus 9090:9090
```

Open `http://127.0.0.1:9090/targets` and confirm the ShelfSense backend targets are up. Verify application samples through the Prometheus query API:

```bash
curl --get 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up{service="shelfsense-backend"}'
curl --get 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=shelfsense_http_requests_total'
```

The expected components are Prometheus, Grafana, Alertmanager, kube-state-metrics, and a node-exporter DaemonSet. Monitoring history and Grafana state are intentionally ephemeral and can be lost when Pods are recreated.
