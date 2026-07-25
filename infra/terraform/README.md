# ShelfSense IT Terraform

This directory contains the Terraform configuration for the AWS infrastructure of the ShelfSense IT project.

## Responsibility boundaries

Terraform is responsible for provisioning AWS infrastructure, including:

- VPC
- Public subnet
- Internet Gateway
- Route Table
- Security Group
- EC2 Instance

Ansible will configure the EC2 instance after Terraform creates it.

Terraform creates infrastructure.

Ansible configures the operating system and installs software.

## Authentication

Terraform uses the standard AWS credential chain.

AWS credentials must never be stored inside the repository.

Supported authentication methods include:

- AWS CLI
- Environment variables
- IAM Roles

## Current milestone

This milestone only creates the Terraform foundation.

No AWS resources are provisioned yet.

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