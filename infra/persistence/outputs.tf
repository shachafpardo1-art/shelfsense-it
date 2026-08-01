output "volume_id" {
  description = "ID of the long-lived PostgreSQL EBS volume. Pass it securely to the runtime Terraform root."
  value       = aws_ebs_volume.postgres_data.id
  sensitive   = true
}

output "availability_zone" {
  description = "Availability Zone that the disposable runtime must use."
  value       = aws_ebs_volume.postgres_data.availability_zone
}
