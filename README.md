# ShelfSense IT

A modern IT inventory management system built with FastAPI and DevOps best practices.

## Tech Stack

- FastAPI
- PostgreSQL
- Docker
- Terraform
- Ansible
- Jenkins
- Kubernetes
- Helm
- Prometheus
- Grafana

## Inventory Setup

Run the latest database migrations:

```bash
alembic upgrade head
```

Seed the development database with sample inventory items:

```bash
python3 -m scripts.seed_items
```

Start the API locally:

```bash
uvicorn app.main:app --reload
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
