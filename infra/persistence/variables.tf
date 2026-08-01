variable "aws_region" {
  description = "AWS region that contains the persistent PostgreSQL volume."
  type        = string
  default     = "eu-central-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must use a valid AWS Region format, for example eu-central-1."
  }
}

variable "availability_zone" {
  description = "Availability Zone for the volume; the disposable EC2 runtime must use the same zone."
  type        = string
  default     = "eu-central-1a"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+[a-z]$", var.availability_zone))
    error_message = "availability_zone must use a valid AWS Availability Zone format, for example eu-central-1a."
  }
}

variable "volume_size" {
  description = "Persistent PostgreSQL EBS volume size in GiB."
  type        = number
  default     = 10

  validation {
    condition = (
      var.volume_size >= 10 &&
      var.volume_size <= 100 &&
      floor(var.volume_size) == var.volume_size
    )
    error_message = "volume_size must be a whole number between 10 and 100 GiB."
  }
}

variable "volume_type" {
  description = "EBS volume type. This persistence design requires gp3."
  type        = string
  default     = "gp3"

  validation {
    condition     = var.volume_type == "gp3"
    error_message = "volume_type must be gp3."
  }
}

variable "project_name" {
  description = "Project naming prefix used for persistent-volume tags."
  type        = string
  default     = "shelfsense-it"
}
