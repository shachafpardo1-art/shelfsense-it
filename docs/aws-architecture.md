# ShelfSense IT AWS Architecture

## Overview

ShelfSense IT uses a simplified AWS architecture designed for a junior DevOps project.

The goal is to demonstrate Infrastructure as Code, Configuration Management, CI/CD, Kubernetes, and Monitoring while keeping cloud costs low.

The current validated baseline uses Terraform to provision AWS infrastructure and Ansible to configure a single Ubuntu EC2 instance for K3s.

Docker Compose remains a local development workflow only. AWS runtime validation is based on K3s with `containerd`, with application images stored in Docker Hub.

The infrastructure workflow for this milestone is temporary by design: apply, validate, capture evidence, and destroy the resources after verification.

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

### Ansible

Ansible configures the Ubuntu server after Terraform creates it. The validated responsibilities for the current baseline are:

- system bootstrap
- 2 GiB swap configuration
- K3s `v1.34.8+k3s1`
- Helm `v3.19.0`
- kubeconfig setup for cluster access

### Kubernetes Runtime

The validated Kubernetes runtime on AWS is K3s with `containerd`. Helm is installed and verified on the host. The final in-cluster ShelfSense deployment on AWS is still part of a later milestone.

### Image Registry

Application container images are stored in Docker Hub for both local and future cluster-based deployment flows.

---

## Planned Final Architecture

The following components remain planned and should not be treated as already deployed in AWS:

- Traefik ingress
- Frontend and backend services exposed internally as `ClusterIP`
- PostgreSQL as a StatefulSet
- Prometheus
- Grafana
- Jenkins

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

        Prometheus, Grafana, and Jenkins remain planned
        for later deployment milestones.
```

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
