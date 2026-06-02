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
