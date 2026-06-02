output "ecr_repository_url" {
  value = aws_ecr_repository.bot.repository_url
}

output "lambda_function_name" {
  value = aws_lambda_function.bot.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.bot.arn
}

output "scheduler_name" {
  value = aws_scheduler_schedule.post.name
}
