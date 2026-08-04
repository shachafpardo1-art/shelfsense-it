# Jenkins CI/CD foundation

## Execution flow

The repository-root `Jenkinsfile` is a Declarative Pipeline for a Jenkins Multibranch Pipeline job. Concurrent builds are disabled and the full run is bounded to 45 minutes.

Every pull request and `main` build checks out the repository, verifies expected files and whitespace, installs backend dependencies into `.ci-venv`, runs `pytest`, installs frontend dependencies with `npm ci`, runs the TypeScript typecheck and production build, and validates both Docker builds. Docker build contexts are the repository root for both images.

Pull requests stop after validation. PR code never receives Docker Hub, Kubernetes, database, or Git push credentials and cannot push, deploy, or tag.

On `main`, Jenkins additionally:

1. Finds the highest strict `vMAJOR.MINOR.PATCH` Git tag and increments its patch. With no matching tag, the first release is `v1.0.0`.
2. Reuses the validation images and tags both backend and frontend with the shared semantic version and the full commit SHA.
3. Logs in to Docker Hub using the Jenkins credential, pushes both tags for both repositories, and logs out during unconditional cleanup.
4. Writes the Jenkins-managed PostgreSQL password to a temporary mode-`0600` file. The value is never echoed; Helm receives it with `--set-file`, supporting both install and upgrade without exposing the password in process arguments.
5. Runs `helm upgrade --install shelfsense kubernetes/helm-chart --namespace shelfsense --atomic --wait --wait-for-jobs --timeout 10m` with the semantic image tag. Helm owns the application resources and namespaced PVC; the external PersistentVolume is not part of the chart.
6. Checks the backend/frontend Deployments and PostgreSQL StatefulSet, then uses local `kubectl port-forward` sessions to test backend `/ready` and the frontend root.
7. Creates and pushes the annotated Git tag only after deployment and smoke tests succeed.

An upgrade failure is rolled back automatically by Helm `--atomic`. A rollout or smoke-test failure prevents the Git tag and triggers `helm rollback shelfsense 0 --namespace shelfsense --wait`, which restores the previous Helm revision before the build fails. If rollback itself fails, the build remains failed and an operator must inspect `helm history` and cluster events before performing a reviewed recovery.

## Jenkins credentials

Configure these credentials in Jenkins; never store their values in Git:

| ID | Jenkins kind | Purpose |
| --- | --- | --- |
| `dockerhub-credentials` | Username with password | Push the backend and frontend images to Docker Hub. |
| `shelfsense-kubeconfig` | Secret file | Namespace-limited Kubernetes authentication for Helm, rollout, and smoke checks. |
| `shelfsense-db-password` | Secret text | The existing PostgreSQL application password, also used on a first installation. |
| `github-credentials` | Username with password | GitHub username plus a narrowly scoped token allowed to push release tags. |

All release credentials are referenced only inside `main`-only stages. Jenkins masks bound values, and shell tracing is disabled while sensitive values are handled.

## Kubernetes bootstrap

The bootstrap is a manual operator action and is not run by Jenkins:

```bash
kubectl apply -f kubernetes/ci/jenkins-rbac.yaml
kubectl auth can-i --as=system:serviceaccount:shelfsense:jenkins-deployer --namespace=shelfsense get deployments
kubectl auth can-i --as=system:serviceaccount:shelfsense:jenkins-deployer create persistentvolumes
scripts/generate_jenkins_kubeconfig.sh
```

The first authorization check should print `yes`; the PersistentVolume check should print `no`. The helper defaults to ServiceAccount `jenkins-deployer`, namespace `shelfsense`, a 24-hour bounded token, and output `kubernetes/ci/generated/shelfsense-kubeconfig`. Override them with positional arguments and `TOKEN_DURATION`, for example:

```bash
TOKEN_DURATION=8h scripts/generate_jenkins_kubeconfig.sh shelfsense jenkins-deployer /tmp/shelfsense-kubeconfig
```

Upload the generated file to Jenkins as **Secret file** with ID **`shelfsense-kubeconfig`**, add the current database password as **Secret text** with ID **`shelfsense-db-password`**, test the pipeline, and then securely delete the local kubeconfig. The database credential must match the password already used by a deployed PostgreSQL instance; changing it only in Helm does not rotate the database role password. Generated default and matching kubeconfig filenames are ignored by Git. Because ServiceAccount tokens expire, regenerate and replace the Jenkins Secret file before its configured lifetime ends. A longer duration may be requested, but the Kubernetes API server can shorten it.

The Role is namespace-scoped. Helm needs discovery-style `get`, `list`, and `watch` over supported namespaced resource types because Helm compares stored release state with live objects; Kubernetes RBAC cannot restrict `create` by `resourceNames`. Write access is therefore limited by namespace and resource type. It does not include namespaces, PersistentVolumes, nodes, cluster roles, custom resource definitions, the monitoring namespace, ServiceMonitors, or PrometheusRules.

## Jenkins job and GitHub webhook

Create a Jenkins Multibranch Pipeline pointed at this repository, configure branch-source credentials as needed, and ensure `main` plus change requests are discovered. The GitHub App/PAT used for branch discovery can be separate from `github-credentials`; only the latter needs tag-push permission.

Webhook setup remains manual: expose a TLS-protected Jenkins webhook endpoint (do not expose port 8080 directly), add the Jenkins GitHub webhook URL to the repository, select push and pull-request events, and verify delivery plus automatic branch indexing. Until that is configured, use manual scans/builds.

## Evidence still required

Capture evidence without exposing secrets:

- successful PR validation showing that release stages were skipped;
- successful `main` run through image push, atomic Helm deployment, smoke tests, and Git tag;
- Docker Hub semantic and immutable image tags for both repositories;
- Kubernetes rollout state and Helm release history;
- RBAC `can-i` checks showing allowed namespaced access and denied PersistentVolume access;
- successful GitHub webhook delivery.
