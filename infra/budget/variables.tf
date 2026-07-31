variable "aws_region" {
  description = "AWS region used by the budget stack provider."
  type        = string
  default     = "eu-central-1"
}

variable "monthly_budget_amount" {
  description = "Monthly AWS cost budget in USD."
  type        = number
  default     = 10

  validation {
    condition     = var.monthly_budget_amount > 0
    error_message = "monthly_budget_amount must be greater than zero."
  }
}

variable "budget_alert_email" {
  description = "Email address that receives AWS Budget notifications."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@ ]+@[^@ ]+[.][^@ ]+$", var.budget_alert_email))
    error_message = "budget_alert_email must be a valid email address."
  }
}
