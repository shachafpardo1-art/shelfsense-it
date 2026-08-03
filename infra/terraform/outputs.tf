output "vpc_id" {
  description = "ID of the ShelfSense VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet."
  value       = aws_subnet.public.id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway."
  value       = aws_internet_gateway.main.id
}

output "public_route_table_id" {
  description = "ID of the public route table."
  value       = aws_route_table.public.id
}

output "security_group_id" {
  description = "ID of the security group attached to the ShelfSense server."
  value       = aws_security_group.shelfsense_server.id
}

output "ec2_instance_id" {
  description = "ID of the ShelfSense EC2 instance."
  value       = aws_instance.shelfsense_server.id
}

output "ec2_public_ip" {
  description = "Stable Elastic IPv4 address associated with the ShelfSense EC2 instance."
  value       = aws_eip.shelfsense_server.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the ShelfSense EC2 instance."
  value       = aws_instance.shelfsense_server.public_dns
}

output "ssh_command" {
  description = "Example SSH command for connecting to the ShelfSense server."
  value       = "ssh -i <PRIVATE_KEY_PATH> ubuntu@${aws_eip.shelfsense_server.public_ip}"
}

output "persistent_postgres_volume_id" {
  description = "ID of the attached PostgreSQL volume, passed through for the ignored Ansible inventory handoff."
  value       = var.persistent_postgres_volume_id
  sensitive   = true
}

output "persistent_postgres_attachment_device_name" {
  description = "Requested EC2 attachment name; the Linux NVMe device is discovered separately by volume ID."
  value       = aws_volume_attachment.postgres_data.device_name
}

output "persistent_jenkins_volume_id" {
  description = "ID of the attached Jenkins controller volume, passed through for the Ansible storage handoff."
  value       = var.persistent_jenkins_volume_id
}

output "persistent_jenkins_attachment_device_name" {
  description = "Requested Jenkins EC2 attachment name; the Linux NVMe device is discovered separately by volume ID."
  value       = aws_volume_attachment.jenkins_data.device_name
}
