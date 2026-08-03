# Project Decisions

## Runtime and CI/CD

- Jenkins and K3s run on the same EC2 instance.
- The server currently provides 2 vCPU, about 8 GiB RAM, 2 GiB swap, and sufficient disk capacity for the planned workload.
- Jenkins uses one executor and does not run builds concurrently.
- Pull requests run CI validation only; deployment occurs only after merge to `main`.
- Releases use one shared version for the backend and frontend in the `1.0.x` series, and both images are rebuilt for every release.
- Helm deployments are atomic and wait for workload readiness. A failed smoke test triggers rollback.
- Jenkins credentials remain outside Git, and Jenkins uses restricted Kubernetes RBAC.

## Stable Public Endpoint

- A Terraform-managed Elastic IP provides a stable endpoint for Jenkins, GitHub webhooks, SSH, and the application.
- The Elastic IP is part of the disposable runtime root and must be released during teardown to avoid ongoing charges.

## Kubernetes Storage Lifecycle

- Jenkins receives restricted namespace RBAC, so the cluster-scoped PostgreSQL PersistentVolume is infrastructure-managed separately from application releases.
- The standalone PV is applied once; the ShelfSense Helm release continues to own the namespaced PersistentVolumeClaim and PostgreSQL StatefulSet.
- The existing cluster completed the Helm keep-policy transition before externalization, so no PV deletion or recreation was required. Normal Helm operations do not manage the PV, and explicit PV or EBS deletion requires a separate destructive decision.

## Jenkins Controller Storage

- Jenkins controller state lives on a dedicated encrypted retained 10 GiB `gp3` EBS volume mounted at `/var/lib/jenkins`, separate from PostgreSQL storage and the disposable runtime state.
- Runtime teardown removes only the Jenkins attachment. After EC2 replacement, the same volume is reattached and remounted before Jenkins starts, preserving plugins, credentials, configuration, and build history.
- Initial formatting is disabled by default and may be authorized only for a verified signature-free new volume. The storage milestone uses temporary `root:root` ownership; the later Jenkins role sets `jenkins:jenkins` after package installation and before first startup.
- Explicit Jenkins EBS deletion requires a separate destructive decision. Retained storage improves lifecycle durability but is not a backup.
- `/var/lib/jenkins` uses an fstab `nofail` mount so a missing Jenkins data disk cannot block the EC2/K3s host from booting.
- Before Jenkins is ever enabled or started, its later systemd role must add `RequiresMountsFor=/var/lib/jenkins`, verify the expected UUID-backed mount, and assign `jenkins:jenkins` ownership. If the retained mount is absent or mismatched, Jenkins remains stopped instead of writing controller state to the EC2 root volume.
