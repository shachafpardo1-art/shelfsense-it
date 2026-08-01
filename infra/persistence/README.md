# ShelfSense persistent PostgreSQL volume

This directory is an independent, long-lived Terraform root. It owns only the encrypted `gp3` EBS volume that stores PostgreSQL data. Its state and lifecycle are intentionally separate from the disposable runtime in `infra/terraform`.

## Lifecycle boundary

Apply this root before creating the runtime. Pass its sensitive `volume_id` output and its `availability_zone` output to the runtime through a local, ignored `infra/terraform/terraform.tfvars` file. Never commit the real volume ID.

Region and Availability Zone inputs are syntax-checked locally, and the EBS resource has a blocking precondition requiring the Availability Zone to belong to the configured Region. The example/default pair remains `eu-central-1` and `eu-central-1a`.

The runtime root owns only the EBS attachment. A normal runtime destroy detaches the volume but does not delete it. Do not destroy this persistence root during routine teardown or EC2 replacement.

`lifecycle.prevent_destroy` is an additional safety guard. It is not the lifecycle boundary: the separate Terraform root and separate state are what keep runtime teardown from owning or deleting the volume.

## Order of operations

Apply:

1. Apply `infra/persistence` after external review.
2. Copy the volume ID and Availability Zone into the ignored runtime tfvars file.
3. Apply `infra/terraform` after external review.
4. Run Ansible to detect and mount an existing ext4 filesystem. For a verified new empty volume, explicitly authorize the one-time format as documented in `ansible/README.md`; the committed default refuses formatting.
5. Deploy the Helm chart.

Destroy:

1. Remove application/runtime resources as appropriate.
2. Destroy `infra/terraform` to detach and remove the disposable runtime.
3. Keep `infra/persistence` intact during normal operation.

The retained EBS volume is not a backup. Explicit persistence destruction, EBS corruption, filesystem corruption, or accidental database deletion can still cause data loss. Database exports or an S3-backed backup layer remain future resilience work.

Do not commit `.terraform/`, state, plans, real tfvars files, or copied volume IDs.
