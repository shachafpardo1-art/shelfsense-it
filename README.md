# ShelfSense IT

A modern IT inventory management system built with FastAPI and DevOps best practices.

## Tech Stack

- FastAPI
- React
- TypeScript
- Vite
- PostgreSQL
- Docker
- Terraform
- Ansible
- Jenkins
- Kubernetes
- Helm
- Prometheus
- Grafana

## Project status

Terraform provisions the disposable AWS runtime and the separately managed retained EBS volumes. Ansible configures the EC2 host, storage mounts, swap, K3s, Helm, Jenkins, and the runtime packages required by Jenkins jobs. ShelfSense is deployed to the single-node K3s cluster through Helm. The internal monitoring stack and the Jenkins Multibranch CI/CD pipeline are operational.

The current design deliberately remains a single-host capstone environment. It does not claim multi-node availability, automated backups, public TLS or DNS, or external Alertmanager notification delivery.

## Architecture overview

The React and TypeScript frontend sends inventory requests to the FastAPI backend, which uses SQLAlchemy and Alembic with PostgreSQL. Nginx serves the production frontend. The backend provides health and database-aware readiness endpoints, Prometheus metrics, and request-correlated logging.

Docker Compose is the local development runtime. In AWS, Terraform provisions the disposable network and EC2 runtime and separately manages retained encrypted PostgreSQL and Jenkins EBS volumes. Ansible configures the Ubuntu host, and Helm deploys ShelfSense to the single-node K3s cluster. Traefik routes application traffic, while `kube-prometheus-stack` monitors the application from the separate `monitoring` namespace.

Jenkins runs on the EC2 host and uses a Multibranch Pipeline. Validation builds do not deploy. Successful `main` builds publish images, deploy through Helm with restricted Kubernetes RBAC, verify the rollout and application, and create the release Git tag.

## Local quick start

```bash
cp .env.example .env
docker compose up --build
```

After the services become ready, open the frontend at `http://127.0.0.1:3000` and the backend API documentation at `http://127.0.0.1:8000/docs`. The Compose `migrate` service applies Alembic migrations and seeds the sample inventory before the backend starts.

## Repository structure

Application code, infrastructure, configuration management, deployment definitions, monitoring, and CI/CD are maintained in this repository. See the [repository guide](docs/repository-guide.md) for a path-by-path map and the connections between major components.

## Documentation index

- [AWS architecture and storage lifecycle](docs/aws-architecture.md)
- [Jenkins CI/CD](docs/jenkins-cicd.md)
- [Project decisions](docs/project-decisions.md)
- [Terraform validation](docs/terraform-validation.md)
- [Repository guide](docs/repository-guide.md)
- [Project retrospective](docs/project-retrospective.md)
- [Evidence index](docs/evidence.md)
- [Monitoring installation and validation](monitoring/README.md)

## Persistent AWS database storage

The disposable AWS runtime and long-lived PostgreSQL data have separate lifecycle owners:

```text
infra/persistence
  -> encrypted persistent EBS volume
infra/terraform
  -> disposable EC2 runtime and EBS attachment
Ansible
  -> Nitro device discovery, ext4 safety checks and UUID mount
Helm/K3s
  -> static PV/PVC over the retained PostgreSQL data mount
```

Apply in this order: `infra/persistence`, `infra/terraform`, Ansible bootstrap, then Helm. During normal teardown, remove the application/runtime as appropriate and destroy only `infra/terraform`; keep `infra/persistence` intact.

The retained volume survives Pod recreation, Helm upgrade, Helm metadata recreation, EC2 replacement, and runtime Terraform destroy/apply cycles when it is reattached in the same Availability Zone. Helm uninstall removes the chart-owned PV/PVC metadata, not the mounted EBS data; the controlled recovery cases are documented in `docs/aws-architecture.md`. Retained EBS does not protect against explicit persistence destruction, EBS/filesystem corruption, or accidental database deletion. It is not a backup; database exports or an S3-backed backup layer remain future resilience work.

The current static `hostPath` design assumes a single-node K3s cluster. `hostPath` storage is node-local, so the PostgreSQL Pod must run on the node where `/srv/shelfsense/postgres` is mounted; it is not suitable for uncontrolled multi-node scheduling. A future multi-node design requires stable node labels with node affinity, or a CSI-backed storage solution such as AWS EBS CSI. Reattaching the retained EBS volume preserves data across replacement of the current single runtime node, but it does not provide multi-node high availability.

## Frontend Overview

The `frontend/` application is a lightweight React dashboard for demonstrating the inventory backend in a portfolio-friendly way. It includes:

- Dashboard summary cards for stock and inventory value
- Inventory table with status badges
- Search and category filtering using the backend query parameters
- Create, edit, and soft-delete item workflows
- Loading, empty, and API error states

## Backend Setup

Run the latest database migrations:

```bash
alembic upgrade head
```

Seed the development database with sample inventory items:

```bash
python3 scripts/seed_items.py
```

Start the API locally:

```bash
uvicorn app.main:app --reload
```

The backend allows browser access from the Vite dev server through the configurable `CORS_ALLOW_ORIGINS` environment variable. Default local origins are:

```bash
http://localhost:5173,http://127.0.0.1:5173
```

## Frontend Setup

Create a frontend environment file:

```bash
cp frontend/.env.example frontend/.env
```

Required frontend environment variable:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Install frontend dependencies:

```bash
cd frontend
npm ci
```

Start the frontend locally:

```bash
npm run dev
```

## Run Backend And Frontend Together

In terminal one:

```bash
uvicorn app.main:app --reload
```

In terminal two:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```

## Dashboard Summary

Fetch the inventory dashboard summary:

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary
```

## Item Filters

Search items by partial name or SKU, case-insensitive:

```bash
curl "http://127.0.0.1:8000/api/v1/items?search=rtx"
```

Filter items by exact category, case-insensitive:

```bash
curl "http://127.0.0.1:8000/api/v1/items?category=gpu"
```

Combine search and category:

```bash
curl "http://127.0.0.1:8000/api/v1/items?search=rtx&category=gpu"
```

## Main Pages

- `/` dashboard summary view
- `/inventory` inventory management view with filters and item CRUD actions

### Database initialization

When the stack starts, the `migrate` service waits for PostgreSQL to become healthy and then initializes the database in the following order:

1. Runs `alembic upgrade head` to apply all database migrations.
2. Runs `python scripts/seed_items.py` to insert the sample inventory data.

The seed script is idempotent and identifies existing items by SKU, so repeated runs do not create duplicates. The backend starts only after database initialization completes successfully.

The Helm deployment uses the same initialization flow through a migration Job configured with the `post-install` and `pre-upgrade` hooks.

## K3s application access

The Helm chart uses the Traefik ingress controller included with K3s as the public HTTP entry point. Both application Services are `ClusterIP` by default, so they remain reachable only inside the cluster. With the default empty ingress host, Traefik accepts requests sent to the EC2 public IP without requiring DNS:

```text
http://<EC2_PUBLIC_IP>/             -> frontend Service
http://<EC2_PUBLIC_IP>/api         -> backend Service
http://<EC2_PUBLIC_IP>/health      -> backend Service
http://<EC2_PUBLIC_IP>/ready       -> backend Service
```

The frontend image defaults to the same-origin API base `/api/v1`. Browser API calls therefore return through Traefik to the backend without a hard-coded hostname or cross-origin configuration. Set `ingress.host` when a DNS name becomes available, or set `ingress.enabled: false` when ingress is managed separately. TLS certificates, HTTPS configuration, and DNS provisioning are not implemented in the current scope.

## K3s monitoring

The lightweight monitoring stack is installed as a separate `kube-prometheus-stack` Helm release in the `monitoring` namespace. Prometheus scrapes the backend `/metrics` endpoint internally through the `shelfsense-backend` ClusterIP Service; Traefik no longer exposes `/metrics` publicly. Grafana remains ClusterIP-only and is accessed with `kubectl port-forward`. Prometheus, Alertmanager, and Grafana storage is ephemeral. Installation and validation commands are in [`monitoring/README.md`](monitoring/README.md).

## Jenkins CI/CD

The root `Jenkinsfile` validates backend, frontend, and container builds for pull requests and branches without exposing release credentials. A successful `main` build publishes shared semantic and immutable image tags, deploys the `shelfsense` Helm release with namespace-restricted Kubernetes access, verifies the rollout, performs local smoke tests, and then creates the release Git tag. Jenkins is bound to loopback and accessed through an SSH tunnel. Public GitHub webhook delivery is intentionally not configured; Multibranch repository scanning and manual scans discover changes. Bootstrap, credentials, RBAC, rollback behavior, and validation evidence are documented in [`docs/jenkins-cicd.md`](docs/jenkins-cicd.md).

## Release and versioning model

Annotated Git tags in the `vMAJOR.MINOR.PATCH` series are the authoritative production release versions. For each successful `main` release, Jenkins publishes both backend and frontend images with the shared semantic version and with the full commit SHA as an immutable tag. Jenkins passes `RELEASE_VERSION` to Helm and overrides `backend.image.tag` and `frontend.image.tag`, so the deployed images correspond to the Git release even when chart defaults differ.

`kubernetes/helm-chart/Chart.yaml` `version` identifies the Helm chart package and schema. Its `appVersion` and the default image tags in `values.yaml` are baseline metadata and fallback values. Component metadata in `app/config.py` and `frontend/package.json` is maintained for those components and does not dynamically follow every Jenkins release.

## Limitations

- The AWS runtime uses one EC2 instance and a single-node K3s cluster; it is not highly available.
- Retained EBS volumes provide persistence across runtime replacement but are not backups.
- TLS and DNS are not configured for application access.
- Jenkins remains loopback-only, so public GitHub webhook delivery is not configured.
- Monitoring storage is ephemeral, and Alertmanager has no external notification receiver.
- PostgreSQL uses node-local static `hostPath` storage rather than CSI-backed dynamic storage.
