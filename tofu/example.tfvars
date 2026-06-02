# Copy to terraform.tfvars (gitignored) and fill in your values.

aws_region = "us-east-1"

# image_uri is set automatically by deploy.sh; set manually only if needed.
# image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/billionaire-matchmaker:abc1234"

# Posting schedule.
# "rate(1 day)"     → once per day (production default)
# "rate(11 minutes)" → ~666-second cadence for demos (hits Bluesky rate limits quickly)
# "cron(0 12 * * ? *)" → noon UTC daily
schedule_expression = "rate(1 day)"
