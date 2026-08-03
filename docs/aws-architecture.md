# ShelfSense IT AWS Architecture

## Overview

ShelfSense IT uses a simplified AWS architecture designed for a junior DevOps project.

The goal is to demonstrate Infrastructure as Code, Configuration Management, CI/CD, Kubernetes, and Monitoring while keeping cloud costs low.

The current validated baseline uses Terraform to provision AWS infrastructure and Ansible to configure a single Ubuntu EC2 instance for K3s.

Docker Compose remains a local development workflow only. AWS runtime validation is based on K3s with `containerd`, with application images stored in Docker Hub.

The compute/network runtime remains temporary. PostgreSQL data and Jenkins controller state have separate long-lived lifecycles on dedicated retained EBS volumes.

---

## Current Validated Baseline

```text
                 Internet
                     |
             Internet Gateway
                     |
              Public Route Table
                     |
               Public Subnet
                     |
              Security Group
                     |
               Ubuntu EC2 Instance
                     |
       Retained EBS volume attachments
              |               |
  /srv/shelfsense/postgres  /var/lib/jenkins
         (ext4, UUID)         (ext4, UUID)
                     |
          K3s v1.34.8+k3s1 (containerd)
                     |
               Helm v3.19.0
                     |
              kubeconfig access
```

### Terraform

Terraform creates the AWS infrastructure baseline:

- VPC
- Public subnet
- Internet gateway
- Route table
- Security group
- EC2 instance
- attachments to existing persistent PostgreSQL and Jenkins EBS volumes

The EBS volumes are created by the independent `infra/persistence` Terraform root and are never declared in the disposable runtime state. Both Terraform roots use the same Availability Zone. Runtime destroy removes the attachments and disposable EC2 resources but retains both persistence volumes.

### Ansible

Ansible configures the Ubuntu server after Terraform creates it. The validated responsibilities for the current baseline are:

- system bootstrap
- 2 GiB swap configuration
- K3s `v1.34.8+k3s1`
- Helm `v3.19.0`
- kubeconfig setup for cluster access
- safe Nitro EBS discovery, first-use ext4 creation, UUID-based fstab entry, and mount at `/srv/shelfsense/postgres`
- safe Nitro EBS discovery, guarded first-use ext4 creation, UUID-based fstab entry, and mount at `/var/lib/jenkins` when a Jenkins volume ID is supplied

Jenkins storage is prepared as `root:root` because the package-created `jenkins` user does not exist during this milestone. The later Jenkins role must set `jenkins:jenkins` ownership after package installation and before the first service start. Jenkins must never start before the retained mount is verified.

### Kubernetes Runtime

The validated Kubernetes runtime on AWS is K3s with `containerd`. Helm is installed and verified on the host. The final in-cluster ShelfSense deployment on AWS is still part of a later milestone.

The infrastructure-managed `kubernetes/infrastructure/postgres-pv.yaml` manifest defines the static PersistentVolume with reclaim policy `Retain`. The Helm chart owns the explicitly bound PersistentVolumeClaim and PostgreSQL StatefulSet backed by `/srv/shelfsense/postgres`. PostgreSQL does not use the default K3s local-path provisioner for the AWS persistence path. The chart pins `postgres:16.14-trixie` so the reviewed PostgreSQL 16 behavior and UID/GID 999 storage contract do not drift with the mutable `postgres:16` tag.

### Single-node hostPath constraint

This persistence model assumes the current single-node K3s cluster. The static `hostPath` volume is node-local, and the PostgreSQL Pod must run on the node where `/srv/shelfsense/postgres` is mounted. The design is therefore not suitable for uncontrolled multi-node scheduling.

A future multi-node design must use stable node labels with node affinity to bind PostgreSQL to the storage node, or replace `hostPath` with a proper CSI-backed storage solution such as AWS EBS CSI. The retained EBS volume preserves data when the current single runtime node is replaced and the volume is reattached and remounted, but it does not provide multi-node high availability. Retained EBS remains persistence, not a backup.

### Persistence lifecycle

Apply order:

1. `infra/persistence` apply
2. `infra/terraform` apply with the reviewed volume-ID/AZ handoff
3. Ansible bootstrap
4. Apply `kubernetes/infrastructure/postgres-pv.yaml` once, after verifying that `/srv/shelfsense/postgres` is the retained mounted filesystem
5. Install the ShelfSense Helm release

Jenkins manages only the namespace-scoped application resources in the Helm release. The cluster-scoped PV is provisioned separately and remains outside the application release lifecycle.

Normal destroy order:

1. Application/runtime teardown as appropriate
2. `infra/terraform` destroy
3. Keep `infra/persistence`; do not destroy it during normal operation

PostgreSQL data and Jenkins plugins, credentials, controller configuration, and build history survive EC2 replacement and disposable runtime destroy/apply cycles when their respective volumes are reattached and remounted. First-time formatting requires explicit authorization and is permitted only for a verified signature-free new volume. Explicit PV or EBS deletion requires a separate destructive decision. Persistent storage is not a backup; independent backups remain a future resilience layer.

### Jenkins controller storage lifecycle

The dedicated encrypted 10 GiB `gp3` Jenkins EBS volume is persistence-managed and mounted at `/var/lib/jenkins`. The runtime Terraform state owns only `aws_volume_attachment.jenkins_data`. After runtime recreation, attach the retained volume, run the guarded Ansible mount workflow, verify the UUID-backed mount, install Jenkins if needed, set final `jenkins:jenkins` ownership, and only then start the service.

A blank Jenkins volume is not formatted by default. An operator must verify the exact EBS identity and explicitly authorize the one-time format; any existing filesystem or ambiguous signature causes a safe failure. Destroying the runtime detaches the volume but does not delete it. Destroying the Jenkins EBS volume remains an explicit persistence-root action and requires a reviewed data-destruction decision.

The `/var/lib/jenkins` fstab entry includes `nofail`, allowing the EC2/K3s host to boot even when the Jenkins data volume is absent. Jenkins must not treat that condition as permission to use the root disk. Before the service is ever enabled or started, the later Jenkins systemd role must configure `RequiresMountsFor=/var/lib/jenkins`, verify the expected UUID-backed mount, and set `jenkins:jenkins` ownership. A missing or mismatched retained mount must keep Jenkins stopped so controller state cannot be written to the disposable EC2 root volume.

### Kubernetes metadata lifecycle and recovery

The EBS filesystem lifecycle and the Kubernetes PV/PVC metadata lifecycle are separate. Neither the standalone PV manifest nor the PVC template formats or deletes the host filesystem. The PV reclaim policy remains `Retain`, but that policy does not prevent an operator from deleting the Kubernetes PV object itself. Explicit PV or EBS deletion requires a separate destructive decision.

- **Pod restart:** the existing bound PVC is reused; no storage metadata is recreated.
- **Helm upgrade:** normal application/configuration upgrades reuse the existing PV/PVC. Treat the PV host path and storage class, and the PVC volume binding, storage class, and access mode as immutable or binding-critical. Do not use an upgrade to change those fields; stop the workload and use controlled metadata recreation instead. Size increases also require a separately reviewed EBS and filesystem growth procedure and are not implemented here.
- **Helm uninstall:** uninstall removes the chart-owned StatefulSet and PVC but does not manage or delete the infrastructure PV. It does not format `/srv/shelfsense/postgres` or delete the underlying EBS volume. A later install creates fresh PVC metadata and explicitly binds it to the existing PV after any stale claim reference is handled safely.
- **Namespace deletion:** deletion removes the namespaced PVC and Helm release records, while the cluster-scoped PV can remain in `Released` with the deleted claim recorded in `spec.claimRef`. `Released` means the prior claim is gone; it does not mean the retained data was erased or that the PV can bind automatically to a new claim.
- **EC2/K3s runtime recreation:** reattach the retained EBS volume in the same Availability Zone, run the controlled Ansible mount workflow, apply the standalone PV manifest, then install the chart into the new cluster. Fresh PV/PVC metadata is created over the remounted data; no Helm ownership adoption is used.
- **Explicit EBS persistence deletion:** this is a separate, destructive operation against `infra/persistence`. It is never part of Helm uninstall, namespace deletion, or disposable runtime teardown, and it requires its own reviewed authorization and backup decision.

Supported recovery after namespace deletion or any leftover `Released` PV:

1. Ensure no PostgreSQL Pod is using the path and verify that the expected retained filesystem is mounted at `/srv/shelfsense/postgres` through the controlled Ansible workflow.
2. Confirm the old PV is `Released`, its reclaim policy is `Retain`, and its claim no longer exists.
3. Delete only the stale Kubernetes PV object. This removes metadata, not the hostPath data or EBS volume.
4. Reapply the standalone PV manifest, recreate the application namespace if needed, and install the chart with the same reviewed persistence values. The chart creates a fresh PVC and binds it explicitly to the PV.
5. Verify the claim is `Bound` and PostgreSQL sees the retained data before resuming normal deployment.

If the PV/PVC name, host path, storage class, access mode, or explicit claim binding must change, use the same stopped-workload metadata-recreation procedure rather than Helm upgrade. This project does not support adopting Helm resources retained from an earlier release.

### Existing-release PV migration

The existing cluster completed a transition Helm release that recorded `helm.sh/resource-policy: keep` before the PV template was removed from the chart. This allowed the retained, bound PV to remain in place without deletion or recreation while application releases became namespace-scoped. Normal Helm upgrades and uninstalls must not delete the PV.

### Image Registry

Application container images are stored in Docker Hub for both local and future cluster-based deployment flows.

---

## K3s Application Architecture

The Helm chart now defines the K3s application routing layer:

- Traefik ingress
- Frontend and backend services exposed internally as `ClusterIP`
- PostgreSQL as a StatefulSet

The monitoring configuration is a separate Helm release in the `monitoring` namespace. Jenkins remains planned and should not be treated as already deployed in AWS.

```text
                 Internet
                     |
                  Traefik
                     |
        +------------+-------------+
        |                          |
   Frontend Service           Backend Service
     (ClusterIP)               (ClusterIP)
                                      |
                                 PostgreSQL
                                (StatefulSet)

        Prometheus scrapes backend metrics internally
        Grafana is available only through port-forward
```

Traefik accepts HTTP requests on the EC2 public IP because the default Ingress rule does not require a host name. It sends `/api` and the operational endpoints `/health` and `/ready` to the backend ClusterIP Service; the catch-all `/` route goes to the frontend ClusterIP Service. The `/metrics` endpoint is not publicly routed. Prometheus reaches it internally through the backend ClusterIP Service and a ServiceMonitor.

Prometheus, Grafana, Alertmanager, kube-state-metrics, and node-exporter are managed by a separate `kube-prometheus-stack` Helm release in the `monitoring` namespace. Grafana is ClusterIP-only and accessed with `kubectl port-forward`. Monitoring storage is ephemeral and does not use the PostgreSQL EBS volume. A configured `ingress.host` narrows public application routing to that DNS host. DNS provisioning and TLS termination are outside this milestone.

## Security Principles

- SSH access should be restricted to an approved IP address.
- Only required ports should be exposed.
- AWS credentials must never be committed to Git.
- Private keys must never be committed.
- Secrets should be managed securely.
- Infrastructure should follow the Principle of Least Privilege.

---

## Project Scope

This project intentionally uses a single EC2 instance.

The purpose is to demonstrate DevOps technologies while remaining within AWS Free Tier and keeping the architecture understandable for a learning project.

A production environment would normally separate workloads across multiple servers or managed AWS services.
