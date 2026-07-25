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
