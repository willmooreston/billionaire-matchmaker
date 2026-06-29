variable "aws_region" {
  type = string
}

variable "project_name" {
  type    = string
  default = "billionaire-matchmaker"
}

variable "image_uri" {
  type        = string
  description = "Full ECR image URI including tag, e.g. 123456789012.dkr.ecr.us-west-2.amazonaws.com/billionaire-matchmaker:abc1234"
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge Scheduler rate or cron expression. Default is once per day."
  default     = "rate(1 day)"
}

variable "schedule_expression_timezone" {
  type        = string
  description = "IANA timezone for the schedule expression. Only meaningful for cron expressions."
  default     = "UTC"
}

variable "alert_email" {
  type        = string
  description = "Email address to receive CloudWatch alarm notifications."
}
