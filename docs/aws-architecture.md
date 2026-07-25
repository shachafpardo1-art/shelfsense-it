# ShelfSense IT AWS Architecture

## Overview

ShelfSense IT uses a simplified AWS architecture designed for a junior DevOps project.

The goal is to demonstrate Infrastructure as Code, Configuration Management, CI/CD, Kubernetes and Monitoring while keeping cloud costs low.

Terraform provisions the AWS infrastructure.

Ansible configures the EC2 instance.

Minikube hosts the Kubernetes cluster.

Helm deploys the ShelfSense application.

Jenkins provides the CI/CD pipeline.

Prometheus and Grafana provide monitoring.

---

## Planned Architecture

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
        +------------+-------------+
        |            |             |
     Jenkins      Minikube      Monitoring
                       |              |
                     Helm     Prometheus
                       |              |
                ShelfSense App     Grafana
                       |
                  PostgreSQL
```

---

## Component Responsibilities

### Terraform

Terraform creates the AWS infrastructure:

- VPC
- Public Subnet
- Internet Gateway
- Route Table
- Security Group
- EC2 Instance

---

### Ansible

Ansible configures the EC2 server after Terraform creates it.

Responsibilities include:

- Docker
- kubectl
- Minikube
- Helm
- Jenkins
- Prometheus
- Grafana

---

### Kubernetes

Minikube hosts the Kubernetes cluster.

Helm manages the deployment of:

- Frontend
- Backend
- PostgreSQL

---

### Jenkins

Jenkins will:

- Build images
- Run automated tests
- Push images to Docker Hub
- Deploy updates to Kubernetes

---

### Monitoring

Prometheus collects metrics.

Grafana visualizes dashboards.

---

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