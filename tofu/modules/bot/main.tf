data "aws_caller_identity" "current" {}

# ── ECR ──────────────────────────────────────────────────────────────────────

resource "aws_ecr_repository" "bot" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "bot" {
  repository = aws_ecr_repository.bot.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# ── DynamoDB history table ────────────────────────────────────────────────────

resource "aws_dynamodb_table" "history" {
  name         = "${var.project_name}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "entity_type"
  range_key    = "entity_id"

  attribute {
    name = "entity_type"
    type = "S"
  }

  attribute {
    name = "entity_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# ── IAM: Lambda execution role ───────────────────────────────────────────────

resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SSMRead"
        Effect = "Allow"
        Action = "ssm:GetParameter"
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/*"
        ]
      },
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:PutItem",
        ]
        Resource = aws_dynamodb_table.history.arn
      },
      {
        Sid    = "Logs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
    ]
  })
}

resource "aws_ecr_repository_policy" "lambda_pull" {
  repository = aws_ecr_repository.bot.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "LambdaPull"
      Effect = "Allow"
      Principal = { AWS = aws_iam_role.lambda.arn }
      Action = [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
      ]
    }]
  })
}

# ── CloudWatch ────────────────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 7
}

# ── SSM Parameters (placeholder values; overwrite before first post) ─────────

resource "aws_ssm_parameter" "bluesky_handle" {
  name  = "/${var.project_name}/bluesky-handle"
  type  = "SecureString"
  value = "placeholder-overwrite-before-first-post"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "bluesky_app_password" {
  name  = "/${var.project_name}/bluesky-app-password"
  type  = "SecureString"
  value = "placeholder-overwrite-before-first-post"

  lifecycle {
    ignore_changes = [value]
  }
}

# ── Lambda function ───────────────────────────────────────────────────────────

resource "aws_lambda_function" "bot" {
  function_name = var.project_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      SSM_PARAM_HANDLE   = aws_ssm_parameter.bluesky_handle.name
      SSM_PARAM_PASSWORD = aws_ssm_parameter.bluesky_app_password.name
      DYNAMODB_TABLE     = aws_dynamodb_table.history.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ── IAM: EventBridge Scheduler execution role ─────────────────────────────────

resource "aws_iam_role" "scheduler" {
  name = "${var.project_name}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.bot.arn
    }]
  })
}

# ── EventBridge Scheduler ─────────────────────────────────────────────────────

resource "aws_scheduler_schedule" "post" {
  name       = "${var.project_name}-post"
  group_name = "default"

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 30
  }

  schedule_expression          = var.schedule_expression
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.bot.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = "{}"
  }
}
