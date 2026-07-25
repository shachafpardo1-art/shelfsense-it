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
