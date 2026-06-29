variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "image_uri" {
  type        = string
  description = "ECR image URI passed by deploy.sh after the image is built and pushed"
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge Scheduler expression. 'rate(1 day)' posts once per day. 'rate(11 minutes)' approximates the 666-second demo cadence."
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
