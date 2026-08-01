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
npm install
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
