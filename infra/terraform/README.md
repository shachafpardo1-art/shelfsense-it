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

Ansible configures the EC2 instance after Terraform creates it, including the operating system baseline and Kubernetes tooling required for this milestone.

## Authentication

Terraform uses the standard AWS credential chain.

AWS credentials must never be stored inside the repository.

Supported authentication methods include:

- AWS CLI
- Environment variables
- IAM Roles

## Current milestone

The current validated flow is:

`terraform init` -> `terraform fmt` -> `terraform validate` -> `terraform plan` -> reviewed `terraform apply` -> SSH access -> bootstrap -> Ansible -> K3s/Helm validation -> evidence capture -> `terraform destroy`

The current defaults use a `t3.micro` instance type and an 8 GB root volume. These values are acceptable for the validated baseline and should be reviewed again in the next milestone.

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

The file `terraform.tfvars.example` is safe to commit.
