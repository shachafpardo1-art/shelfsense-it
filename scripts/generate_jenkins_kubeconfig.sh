#!/usr/bin/env bash
set -Eeuo pipefail

namespace="${1:-shelfsense}"
service_account="${2:-jenkins-deployer}"
duration="${TOKEN_DURATION:-24h}"
output_file="${3:-kubernetes/ci/generated/shelfsense-kubeconfig}"

umask 077
mkdir -p "$(dirname "$output_file")"

if [[ -e "$output_file" ]]; then
  printf 'Refusing to overwrite existing file: %s\n' "$output_file" >&2
  exit 1
fi

cluster_name="$(kubectl config view --minify -o jsonpath='{.clusters[0].name}')"
detected_api_server="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
api_server="${KUBERNETES_API_SERVER:-$detected_api_server}"
ca_data="$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')"

if [[ -z "$cluster_name" ]]; then
  echo 'The current kubectl context does not contain a cluster name.' >&2
  exit 1
fi

if [[ -z "$api_server" ]]; then
  echo 'No Kubernetes API server was selected from the current context or KUBERNETES_API_SERVER.' >&2
  exit 1
fi

if [[ "$api_server" != https://* ]]; then
  echo 'The selected Kubernetes API server must start with https://.' >&2
  exit 1
fi

if [[ -z "$ca_data" ]]; then
  ca_file="$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority}')"
  if [[ -z "$ca_file" || ! -r "$ca_file" ]]; then
    echo 'The current kubectl context does not contain readable certificate authority data.' >&2
    exit 1
  fi
  ca_data="$(base64 < "$ca_file" | tr -d '\n')"
fi

token="$(kubectl --namespace "$namespace" create token "$service_account" --duration "$duration")"
cleanup_on_exit() {
  status=$?
  trap - EXIT
  unset token
  if [[ "$status" -ne 0 ]]; then
    rm -f "$output_file"
  fi
  exit "$status"
}
trap cleanup_on_exit EXIT

cat > "$output_file" <<EOF
apiVersion: v1
kind: Config
clusters:
  - name: ${cluster_name}
    cluster:
      server: ${api_server}
      certificate-authority-data: ${ca_data}
users:
  - name: ${service_account}
    user:
      token: ${token}
contexts:
  - name: ${service_account}@${cluster_name}
    context:
      cluster: ${cluster_name}
      user: ${service_account}
      namespace: ${namespace}
current-context: ${service_account}@${cluster_name}
EOF

chmod 600 "$output_file"
unset token
trap - EXIT

printf 'Created restricted kubeconfig at %s (mode 0600).\n' "$output_file"
printf 'Selected Kubernetes API server: %s\n' "$api_server"
echo 'Upload it to Jenkins as a Secret file with ID: shelfsense-kubeconfig'
echo 'After upload, delete the local file securely; never commit it.'
