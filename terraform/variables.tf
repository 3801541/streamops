variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-3"  # Paris
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "streamops"
}

variable "environment" {
  description = "Deployment environment (staging | prod)"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "Environment must be 'staging' or 'prod'."
  }
}

variable "db_password" {
  description = "RDS master password — inject via TF_VAR_db_password or AWS Secrets Manager"
  type        = string
  sensitive   = true
}
