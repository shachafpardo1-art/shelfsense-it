#!/usr/bin/env bash
set -Eeuo pipefail

TMP_INVENTORY_FILE=""
SSH_KEY=""

log() {
  printf '[bootstrap] %s\n' "$*"
}

fail() {
  printf '[bootstrap] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

cleanup() {
  if [[ -n "$TMP_INVENTORY_FILE" && -f "$TMP_INVENTORY_FILE" ]]; then
    rm -f "$TMP_INVENTORY_FILE"
  fi
}

sanitize_command() {
  local command_text="$1"
  if [[ -n "$SSH_KEY" ]]; then
    command_text="${command_text//"$SSH_KEY"/[REDACTED]}"
  fi
  printf '%s' "$command_text"
}

on_err() {
  local line_number="$1"
  local command_text
  command_text="$(sanitize_command "$2")"
  printf '[bootstrap] ERROR: command failed at line %s: %s\n' "$line_number" "$command_text" >&2
}

main() {
  if [[ $# -ne 1 ]]; then
    fail "Usage: $0 /path/to/private-key.pem"
  fi

  local script_dir repo_root terraform_dir ansible_dir inventory_file vars_file
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
  terraform_dir="$repo_root/infra/terraform"
  ansible_dir="$repo_root/ansible"
  inventory_file="$ansible_dir/inventory/hosts.ini"
  vars_file="$ansible_dir/inventory/group_vars/all.yml"
  SSH_KEY="$1"

  require_cmd terraform
  require_cmd ansible
  require_cmd ansible-playbook
  require_cmd ssh
  require_cmd ssh-keygen
  require_cmd python3
  require_cmd mktemp
  require_cmd stat
  require_cmd awk
  require_cmd grep

  [[ -f "$SSH_KEY" ]] || fail "SSH private key does not exist: $SSH_KEY"
  [[ -r "$SSH_KEY" ]] || fail "SSH private key is not readable: $SSH_KEY"

local key_mode
key_mode="$(stat -c '%a' "$SSH_KEY")"

case "$key_mode" in
  400|600)
    ;;
  *)
    fail "SSH private key permissions must restrict group/other access: $SSH_KEY has mode $key_mode"
    ;;
esac

  [[ -d "$terraform_dir" ]] || fail "Terraform directory not found: $terraform_dir"
  [[ -d "$ansible_dir" ]] || fail "Ansible directory not found: $ansible_dir"
  [[ -f "$vars_file" ]] || fail "Shared Ansible variables file not found: $vars_file"
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"

  local k3s_version helm_version
  mapfile -t versions < <(
    python3 - "$vars_file" <<'PY'
import pathlib
import sys
import yaml

data = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text())
print(data["k3s_version"])
print(data["helm_version"])
PY
  ) || fail "Unable to read pinned versions from $vars_file"
  k3s_version="${versions[0]:-}"
  helm_version="${versions[1]:-}"
  [[ -n "$k3s_version" ]] || fail "Unable to read k3s_version from $vars_file"
  [[ -n "$helm_version" ]] || fail "Unable to read helm_version from $vars_file"

  log "Reading EC2 public IP from Terraform outputs"
  local server_ip
  server_ip="$(terraform -chdir="$terraform_dir" output -raw ec2_public_ip 2>/dev/null || true)"
  [[ -n "$server_ip" ]] || fail "Terraform output ec2_public_ip is empty"
  [[ "$server_ip" != "null" ]] || fail "Terraform output ec2_public_ip is null"
  [[ "$server_ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || fail "Terraform output is not a valid IPv4 address: $server_ip"
  awk -F. 'NF != 4 { exit 1 } { for (i = 1; i <= 4; i++) if ($i < 0 || $i > 255) exit 1 }' <<<"$server_ip" \
    || fail "Terraform output is not a valid IPv4 address: $server_ip"

  log "Generating Ansible inventory atomically"
  TMP_INVENTORY_FILE="$(mktemp "$ansible_dir/inventory/hosts.ini.tmp.XXXXXX")"
  chmod 600 "$TMP_INVENTORY_FILE"
  cat >"$TMP_INVENTORY_FILE" <<EOF
[production]
shelfsense-server ansible_host=$server_ip ansible_port=22 ansible_user=ubuntu
EOF
  mv "$TMP_INVENTORY_FILE" "$inventory_file"
  TMP_INVENTORY_FILE=""

  local ssh_opts=(
    -i "$SSH_KEY"
    -o BatchMode=yes
    -o ConnectTimeout=10
    -o StrictHostKeyChecking=accept-new
    -o UserKnownHostsFile="$HOME/.ssh/known_hosts"
  )

  log "Waiting for SSH to become available"
  local attempt max_attempts ssh_output
  attempt=1
  max_attempts=30
  while (( attempt <= max_attempts )); do
    ssh_output="$(ssh "${ssh_opts[@]}" "ubuntu@$server_ip" true 2>&1)" && break
    if grep -Eq 'REMOTE HOST IDENTIFICATION HAS CHANGED|Host key verification failed|Offending .* key in' <<<"$ssh_output"; then
      fail "SSH host key mismatch detected for $server_ip. Review the host key and, if valid, run: ssh-keygen -R $server_ip"
    fi
    if (( attempt == max_attempts )); then
      break
    fi
    sleep 10
    ((attempt++))
  done
  (( attempt <= max_attempts )) || fail "SSH did not become available after $max_attempts attempts"

  log "Verifying non-interactive SSH connectivity"
  ssh "${ssh_opts[@]}" "ubuntu@$server_ip" "printf 'connected\n'" >/dev/null || fail "SSH connectivity test failed"

  log "Running Ansible syntax check"
  (
    cd "$ansible_dir"
    ansible-playbook -i inventory/hosts.ini --syntax-check playbooks/site.yml
  )

  log "Running Ansible ping"
  (
    cd "$ansible_dir"
    ansible -i inventory/hosts.ini production -m ping --private-key "$SSH_KEY"
  )

  log "Running Ansible playbook"
  (
    cd "$ansible_dir"
    ansible-playbook -i inventory/hosts.ini playbooks/site.yml --private-key "$SSH_KEY"
  )

  log "Verifying K3s service state"
  (
    cd "$ansible_dir"
    ansible -i inventory/hosts.ini production -b -m command -a "systemctl is-active k3s" --private-key "$SSH_KEY"
  )

  log "Verifying K3s version"
  (
    cd "$ansible_dir"
    ansible -i inventory/hosts.ini production -b -m command -a "bash -lc '/usr/local/bin/k3s --version | grep -F \"$k3s_version\"'" --private-key "$SSH_KEY"
  )

  log "Verifying Kubernetes node readiness"
  (
    cd "$ansible_dir"
    ansible -i inventory/hosts.ini production -b -m command -a "bash -lc '/usr/local/bin/k3s kubectl get nodes --no-headers | grep -w Ready'" --private-key "$SSH_KEY"
  )

  log "Verifying Helm version"
  (
    cd "$ansible_dir"
    ansible -i inventory/hosts.ini production -m command -a "bash -lc '/usr/local/bin/helm version --short | grep -F \"$helm_version\"'" --private-key "$SSH_KEY"
  )

  log "Bootstrap completed successfully"
}

trap cleanup EXIT
trap 'on_err "$LINENO" "$BASH_COMMAND"' ERR

main "$@"
