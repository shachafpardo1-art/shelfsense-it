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
