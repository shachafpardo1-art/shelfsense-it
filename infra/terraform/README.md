# ShelfSense IT Terraform

This directory contains the Terraform configuration for the AWS infrastructure of the ShelfSense IT project.

## Responsibility boundaries

Terraform provisions the AWS infrastructure baseline, including:

- VPC
- Public subnet
- Internet Gateway
- Route Table
- Security Group
- EC2 Instance
- Attachment of the existing PostgreSQL EBS volume owned by `infra/persistence`

Ansible configures the EC2 instance after Terraform creates it, including the operating system baseline and Kubernetes tooling required for this milestone.

## Authentication

Terraform uses the standard AWS credential chain.

AWS credentials must never be stored inside the repository.

Supported authentication methods include:

- AWS CLI
- Environment variables
- IAM Roles

## Current milestone

The runtime is disposable, but PostgreSQL storage is not. The long-lived encrypted EBS volume is declared only in `infra/persistence`; this root receives its volume ID and Availability Zone through local ignored inputs and owns only `aws_volume_attachment.postgres_data`.

Region and Availability Zone inputs are syntax-checked, and blocking resource preconditions require the runtime zone to belong to the configured Region and to exactly match the persistence handoff zone.

The apply flow is:

1. Apply `infra/persistence` after external review.
2. Put its volume ID and Availability Zone into the ignored runtime `terraform.tfvars` file.
3. Apply this runtime root after external review.
4. Run bootstrap/Ansible so the exact Nitro device is mounted at `/srv/shelfsense/postgres`.
5. Deploy the Helm chart so PostgreSQL uses the retained mount.

The normal destroy flow is:

1. Remove application/runtime resources as appropriate.
2. Destroy this runtime root, which removes the attachment and disposable infrastructure.
3. Do not destroy `infra/persistence` during normal teardown.

The previous validated runtime flow was:

`terraform init` -> `terraform fmt` -> `terraform validate` -> `terraform plan` -> reviewed `terraform apply` -> SSH access -> bootstrap -> Ansible -> K3s/Helm validation -> evidence capture -> `terraform destroy`

The temporary, cost-controlled lab runtime uses an `m7i-flex.large` instance with 2 vCPU and 8 GiB RAM. It is x86_64 and compatible with the existing Ubuntu 22.04 amd64, K3s, containerd, Docker images, and Helm baseline.

The root disk is a configurable 30 GiB encrypted `gp3` volume. Ansible separately provides the persistent 2 GiB swap configuration.

The `m7i-flex.large` instance was verified as Free Tier eligible for this project account and is offered in `eu-central-1a`. It was selected after AWS rejected `t3a.large` because the account restricts EC2 launches to Free Tier eligible instance types. This eligibility statement applies to the active project account and is not a general claim for every AWS account.

The persistent `infra/budget` and `infra/persistence` stacks remain separate from this temporary runtime stack. Destroy the runtime when it is not actively being used, and have every Terraform plan externally reviewed before apply. Runtime destroy does not own or delete the retained PostgreSQL EBS volume.

## Common commands

```bash
terraform init
terraform fmt
terraform validate
terraform plan
```

## Repository safety

Do not commit:

- .terraform/
- *.tfstate
- *.tfstate.*
- Real *.tfvars files
- Real EBS volume IDs or generated handoff files

The file `terraform.tfvars.example` is safe to commit.
