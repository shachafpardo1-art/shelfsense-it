# Repository guide

## Overview

ShelfSense IT combines an inventory application with its local runtime, AWS infrastructure, host configuration, Kubernetes deployment, monitoring, and CI/CD definitions. The repository keeps application code and operational configuration together so a reviewer can trace a change from source code through validation and deployment.

## Repository structure

| Path | Purpose |
| --- | --- |
| `app/` | FastAPI application code, SQLAlchemy models and services, API routers, configuration, metrics, and request-correlated logging. |
| `frontend/` | React and TypeScript user interface built with Vite and served by Nginx in the container image. |
| `tests/` | Backend tests for health, readiness, inventory behavior, and observability. |
| `alembic/` | Alembic migration environment and versioned database migrations. |
| `docker/` | Backend and frontend image definitions plus the frontend Nginx configuration. |
| `docker-compose.yml` | Local frontend, backend, PostgreSQL, and database-initialization workflow. |
| `infra/` | Separate Terraform roots for the disposable AWS runtime, retained encrypted storage, and AWS budget configuration. |
| `ansible/` | Host inventory, variables, playbooks, and roles for Ubuntu, storage, swap, Docker, K3s, Helm, and Jenkins. |
| `kubernetes/` | Jenkins RBAC, the infrastructure-managed PostgreSQL PersistentVolume, and the ShelfSense Helm chart. |
| `monitoring/` | `kube-prometheus-stack` values, backend scrape configuration, alert rules, Grafana dashboard definitions, and installation guidance. |
| `scripts/` | Host bootstrap, Jenkins kubeconfig generation, and idempotent inventory seeding helpers. |
| `docs/` | Architecture, CI/CD, decisions, validation, evidence, and retrospective documentation. |
| `Jenkinsfile` | Multibranch validation and `main` release pipeline. |
| `requirements.txt` | Backend runtime Python dependencies. |
| `requirements-dev.txt` | Backend development and test dependencies layered on the runtime requirements. |

## How the parts connect

```text
React frontend --> FastAPI backend API --> PostgreSQL
                         |
                         +--> /metrics <-- Prometheus

Jenkins --> Docker Hub --> Helm --> ShelfSense on K3s

Terraform --> AWS resources
Ansible   --> EC2 operating system and runtime configuration
```

The local Compose workflow builds the frontend and backend images, starts PostgreSQL, runs Alembic migrations and seed data through the `migrate` service, and then starts the application services. Nginx serves the frontend and proxies `/api/` requests to the backend.

In AWS, Terraform creates the disposable network and EC2 runtime and attaches persistence-managed PostgreSQL and Jenkins EBS volumes. Ansible safely mounts those volumes before configuring the single-node K3s runtime and loopback-only Jenkins service.

Jenkins validates pull requests and branches without release credentials. A successful `main` build publishes semantic and immutable images to Docker Hub, deploys the namespaced Helm release to K3s, validates the workloads, and creates the annotated Git release tag. Prometheus independently scrapes backend metrics inside the cluster.
