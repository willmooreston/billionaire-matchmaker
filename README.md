# billionaire-matchmaker

A Bluesky bot that takes a random US billionaire's net worth, finds a random US charity whose annual
budget that fortune would fund for 100+ years, shows the math with cited sources, and closes with a
public-domain quote.

**Stack:** Python 3.14 · AWS Lambda (container image) · EventBridge Scheduler · SSM Parameter Store
· OpenTofu · GitHub Actions

## Sample post

```
Elon Musk has a net worth of $300B as of 2025 (source: Forbes).

That's 2,142 years of funding for Meals On Wheels America ($140M/yr budget).

"Of all forms of tyranny the least attractive and the most vulgar is the
tyranny of mere wealth, the tyranny of a plutocracy." — Theodore Roosevelt, 1906

#eattherich
```

## Architecture

```
EventBridge Scheduler (daily)
        │
        ▼
AWS Lambda  ──── SSM Parameter Store (Bluesky credentials)
(Python 3.14     ├── data/billionaires.json (bundled, ~100 US billionaires)
 container)      ├── ProPublica Nonprofit Explorer API (charity data)
        │        └── data/quotes.json (bundled, ~75 public-domain quotes)
        ▼
   bsky.social (AT Protocol)
        │
        ▼
CloudWatch Logs (/aws/lambda/billionaire-matchmaker)
```

All AWS services stay within the free tier.

## Setup

### 1. Prerequisites

- AWS CLI configured with an account (same account as bedrockconnect-aws is fine)
- Docker Desktop running
- OpenTofu installed (`brew install opentofu`)
- A Bluesky account for the bot

### 2. Bootstrap (one-time)

Creates the S3 state bucket, GitHub OIDC provider, and GitHub Actions IAM role.

```bash
cd tofu/modules/bootstrap

# If the GitHub OIDC provider already exists (e.g. from bedrockconnect-aws),
# leave create_oidc_provider = false (the default).
# If this is a fresh account, add: -var create_oidc_provider=true

tofu init
tofu apply -var 'github_repo=YOUR_GITHUB_USERNAME/billionaire-matchmaker'
```

Copy the output `github_actions_role_arn` and add it as a GitHub Actions secret named
`AWS_ROLE_ARN` in this repository's settings.

### 3. Deploy

```bash
# Copy and fill in terraform.tfvars
cp tofu/example.tfvars tofu/terraform.tfvars

./deploy.sh
```

`deploy.sh` will:
1. Ensure the ECR repository exists
2. Build the Python 3.14 Lambda container image
3. Push it to ECR
4. Run `tofu apply` to create/update all infrastructure

### 4. Set Bluesky credentials

Create a Bluesky app password: **Settings → Privacy and Security → App Passwords**

```bash
aws ssm put-parameter \
  --name /billionaire-matchmaker/bluesky-handle \
  --value "yourbot.bsky.social" \
  --type SecureString --overwrite

aws ssm put-parameter \
  --name /billionaire-matchmaker/bluesky-app-password \
  --value "xxxx-xxxx-xxxx-xxxx" \
  --type SecureString --overwrite
```

### 5. Test

```bash
aws lambda invoke \
  --function-name billionaire-matchmaker \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/out.json && cat /tmp/out.json
```

Or use the **Post Now** button in GitHub Actions → post-now workflow.

## Posting cadence

Set in `tofu/terraform.tfvars`:

```hcl
schedule_expression = "rate(1 day)"         # production default
schedule_expression = "rate(11 minutes)"    # ~666-second demo cadence
schedule_expression = "cron(0 12 * * ? *)"  # noon UTC daily
```

Redeploy with `./deploy.sh` after changing.

## Data maintenance

`lambda/data/billionaires.json` is a Forbes snapshot from 2025. Update it annually after Forbes
publishes its new list. Net worths are intentionally static — no live scraping.

`lambda/data/quotes.json` contains ~75 pre-1928 public-domain quotes.

## Skills demonstrated

| Skill | Implementation |
|---|---|
| IaC (OpenTofu/Terraform) | Modular design in `tofu/modules/` |
| Serverless | Lambda container image via ECR |
| Event-driven architecture | EventBridge Scheduler |
| Secrets management | SSM Parameter Store SecureString, least-privilege IAM |
| CI/CD | GitHub Actions with OIDC (no stored credentials) |
| Observability | Structured JSON logging to CloudWatch |
| Python | API integration (ProPublica, AT Protocol), data wrangling |
| Cost awareness | All services within AWS free tier |
