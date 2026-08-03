variable "project_name" {
  description = "Name of the project used for resource naming and tagging."
  type        = string
  default     = "shelfsense-it"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region where infrastructure will be provisioned."
  type        = string
  default     = "eu-central-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must use a valid AWS Region format, for example eu-central-1."
  }
}

variable "owner" {
  description = "Owner tag used to identify responsibility for the resources."
  type        = string
  default     = "shelfsense-team"
}

variable "vpc_cidr" {
  description = "CIDR block for the ShelfSense VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability Zone for the public subnet."
  type        = string
  default     = "eu-central-1a"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+[a-z]$", var.availability_zone))
    error_message = "availability_zone must use a valid AWS Availability Zone format, for example eu-central-1a."
  }
}
variable "ssh_allowed_cidr" {
  description = "CIDR block allowed to connect to the EC2 instance over SSH."
  type        = string

  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0))
    error_message = "ssh_allowed_cidr must be a valid CIDR block, for example 203.0.113.10/32."
  }
}

variable "key_pair_name" {
  description = "Name of an existing AWS EC2 key pair used for SSH access."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type used for the ShelfSense server."
  type        = string
  default     = "m7i-flex.large"
}

variable "root_volume_size" {
  description = "Size in GiB of the encrypted EC2 root gp3 volume."
  type        = number
  default     = 30

  validation {
    condition = (
      var.root_volume_size >= 8 &&
      var.root_volume_size <= 100 &&
      floor(var.root_volume_size) == var.root_volume_size
    )
    error_message = "root_volume_size must be a whole number between 8 and 100 GiB."
  }
}

variable "persistent_postgres_volume_id" {
  description = "ID of the existing PostgreSQL EBS volume owned by infra/persistence."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^vol-[0-9a-f]{8,17}$", var.persistent_postgres_volume_id))
    error_message = "persistent_postgres_volume_id must be a valid EBS volume ID."
  }
}

variable "persistent_postgres_availability_zone" {
  description = "Availability Zone reported by infra/persistence; it must match the runtime Availability Zone."
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+[a-z]$", var.persistent_postgres_availability_zone))
    error_message = "persistent_postgres_availability_zone must use a valid AWS Availability Zone format, for example eu-central-1a."
  }
}

variable "persistent_postgres_attachment_device_name" {
  description = "Requested EC2 attachment name. Nitro exposes the volume under an NVMe name that Ansible discovers by volume ID."
  type        = string
  default     = "/dev/sdf"

  validation {
    condition     = can(regex("^/dev/sd[f-p]$", var.persistent_postgres_attachment_device_name))
    error_message = "persistent_postgres_attachment_device_name must be an EC2 device name from /dev/sdf through /dev/sdp."
  }
}

variable "persistent_jenkins_volume_id" {
  description = "ID of the existing Jenkins controller EBS volume owned by infra/persistence."
  type        = string

  validation {
    condition     = can(regex("^vol-[0-9a-f]{8,17}$", var.persistent_jenkins_volume_id))
    error_message = "persistent_jenkins_volume_id must be a non-empty valid EBS volume ID."
  }
}

variable "persistent_jenkins_attachment_device_name" {
  description = "Requested EC2 attachment name for Jenkins data. Nitro exposes the volume under an NVMe name discovered by volume ID."
  type        = string
  default     = "/dev/sdg"

  validation {
    condition     = can(regex("^/dev/sd[f-p]$", var.persistent_jenkins_attachment_device_name))
    error_message = "persistent_jenkins_attachment_device_name must be an EC2 device name from /dev/sdf through /dev/sdp."
  }
}
