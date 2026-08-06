# Project retrospective

## Challenges

### Readiness needed a real dependency check

- **What happened:** The initial readiness endpoint could report ready without verifying that the backend could reach PostgreSQL.
- **Why it mattered:** A superficial success response could send traffic to an application that could not perform its core database operations.
- **How it was resolved:** `/ready` now executes `SELECT 1` through SQLAlchemy and returns HTTP 503 when the database is unavailable. `/health` remains a lightweight process-health endpoint.
- **What was learned:** Liveness and readiness answer different questions; readiness must test the dependency required to serve useful traffic.

### Disposable compute and retained state required separate lifecycles

- **What happened:** EC2 needed to remain disposable while PostgreSQL data and Jenkins controller state had to survive runtime replacement.
- **Why it mattered:** Keeping volumes in the runtime Terraform state would make normal teardown risk deleting stateful data or controller configuration.
- **How it was resolved:** Separate Terraform persistence state owns encrypted PostgreSQL and Jenkins EBS volumes. The disposable runtime state owns EC2 and volume attachments only.
- **What was learned:** Resource ownership should follow lifecycle boundaries. Persistence improves durability across replacement, but it is not a backup.

### Nitro EBS device discovery had to be safe and repeatable

- **What happened:** Requested EC2 attachment names do not reliably identify the final NVMe device exposed by Nitro instances.
- **Why it mattered:** Formatting or mounting the wrong block device could destroy data or place persistent state on the disposable root filesystem.
- **How it was resolved:** Ansible resolves the expected EBS identity, checks device topology and signatures, permits first formatting only with explicit authorization, and mounts by filesystem UUID. Jenkins startup is blocked until its retained mount is verified.
- **What was learned:** Storage automation must prove identity and state before mutation, especially around formatting and service startup.

### A manually installed Jenkins dependency broke reproducibility

- **What happened:** The first Jenkins build could not run `python3 -m venv .ci-venv` because `python3-venv` had been installed manually rather than by configuration management.
- **Why it mattered:** A replacement EC2 host would repeat the failure even though the existing host appeared healthy.
- **How it was resolved:** `python3-venv` was added to the centralized Ansible-managed Jenkins runtime package list, installed before Jenkins can execute pipelines.
- **What was learned:** A successful manual repair is not complete until the dependency is represented in the reproducible host definition.

### Jenkins deployment access needed least-privilege RBAC

- **What happened:** Helm requires broad discovery over several namespaced resource types, while the PostgreSQL PersistentVolume is cluster-scoped and must remain infrastructure-managed.
- **Why it mattered:** Giving Jenkins cluster-admin access would unnecessarily expand the impact of a compromised credential or pipeline.
- **How it was resolved:** Jenkins uses a namespace-restricted kubeconfig and RBAC permissions for supported resources in `shelfsense`; cluster-scoped PersistentVolume and monitoring access remain denied.
- **What was learned:** Least privilege is often expressed through namespace and resource-type boundaries rather than a single minimal verb.

### Docker Hub failed during image publication

- **What happened:** A temporary Docker Hub HTTP 502 caused the image-push stage to fail.
- **Why it mattered:** A partial release must not deploy uncertain images or create a Git tag that falsely signals success.
- **How it was resolved:** Pipeline ordering kept Helm deployment and Git tagging skipped. Rerunning the same `main` commit after recovery completed the intended release because no release tag had been created.
- **What was learned:** Safe CI/CD depends on failure containment and ordering, not only on the successful path.

### Several version numbers described different things

- **What happened:** Helm chart version, chart `appVersion`, component metadata, default image tags, semantic releases, and commit-SHA image tags could appear inconsistent.
- **Why it mattered:** Reviewers and operators need to know which value identifies the deployed production release.
- **How it was resolved:** Annotated Git release tags are authoritative. Jenkins publishes matching semantic tags and immutable full-commit-SHA tags, then overrides Helm image tags during deployment; chart and component versions retain their narrower meanings.
- **What was learned:** Versioning becomes understandable when each identifier has one documented owner and purpose.

### The workflow matured from implementation-first to plan-first

- **What happened:** Early work sometimes began with implementation before lifecycle, failure modes, validation, and evidence were fully mapped.
- **Why it mattered:** Infrastructure changes are harder to reverse safely, and late discovery of missing dependencies or evidence creates avoidable rework.
- **How it was resolved:** Later work used explicit scope, verified facts, ordered implementation steps, validation commands, and final diff review before delivery.
- **What was learned:** A short plan improves both execution speed and safety by making assumptions, boundaries, and proof requirements visible early.

## Lessons learned

- **Infrastructure reproducibility:** Manual host repairs must be converted into Terraform, Ansible, or repository-managed configuration.
- **Idempotency:** Repeated Ansible, migration, seeding, Helm, and recovery operations should converge safely rather than duplicate state.
- **Least privilege:** Jenkins needs only namespaced deployment access; infrastructure and monitoring administration remain separate.
- **Health checks:** A process can be alive while its required dependency is unavailable, so readiness must test real service capability.
- **Persistence versus backup:** Retained EBS volumes survive runtime replacement but do not protect against corruption, deletion, or operator error.
- **Safe CI/CD failure:** Publishing, deployment, verification, and tagging order determines whether an external failure remains recoverable.
- **Planning before implementation:** Defining lifecycle, rollback, validation, and scope first reduces risky iteration.
- **Documentation and evidence:** Architecture explanations, limitations, and proof artifacts are engineering deliverables, not post-project decoration.

## Future improvements

The following items are not implemented in the current project:

- provision DNS and TLS for application access;
- expose only the required Jenkins webhook endpoint through a TLS-protected reverse proxy;
- add independently stored and regularly tested PostgreSQL backups;
- add persistent monitoring storage;
- configure a real external Alertmanager notification receiver;
- move from single-node to multi-node Kubernetes where availability requirements justify it;
- replace static `hostPath` storage with CSI-backed storage;
- introduce Kubernetes NetworkPolicies;
- define stricter container `securityContext` settings and non-root workloads;
- plan compatible dependency migrations for React Router and Vite/esbuild;
- add container image vulnerability scanning; and
- strengthen release automation where it can preserve the current ordering, rollback, and immutable-tag guarantees.
