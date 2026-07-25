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
  default     = "t3.micro"
}