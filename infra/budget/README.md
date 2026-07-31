# ShelfSense AWS Budget

This Terraform stack manages the persistent AWS cost-protection budget. It intentionally uses separate Terraform state and lifecycle from `infra/terraform`, so the budget remains active when the temporary EC2/VPC laboratory is destroyed.

Store the real notification email only in the ignored `terraform.tfvars` file. Never commit it.

## Workflow

`terraform init` -> `terraform fmt` -> `terraform validate` -> `terraform plan` -> reviewed `terraform apply`

Do not run `terraform destroy` casually because it removes the budget protection. AWS Budget alerts notify about spending but do not automatically stop EC2 resources.

## Future evidence

- `docs/screenshots/aws/01-budget-terraform-apply.png`
- `docs/screenshots/aws/02-budget-alert-active.png`
