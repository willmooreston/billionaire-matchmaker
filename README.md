# billionaire-matchmaker

A daily Bluesky bot that picks a random US billionaire, finds a charity their net worth
would fund for 100+ years, and shows the math — with a public-domain anti-greed quote
attached as an image. Posts once a day to [@billionaire-match.bsky.social](https://bsky.app/profile/billionaire-match.bsky.social).

**Stack:** Python 3.14 · AWS Lambda (container image) · Amazon ECR · EventBridge Scheduler
· SSM Parameter Store · OpenTofu · GitHub Actions (OIDC)

## Sample post

> Stan Kroenke has a net worth of $15B as of 2025 (source: Forbes).
>
> That's 136 years of funding for Brennan Center for Justice ($110.5M/yr budget, 2023 data).
>
> #eattherich

A quote image (1200×630 PNG) is attached to every post. Replies are disabled.

## Architecture

```
EventBridge Scheduler (rate: 1 day)
        │
        ▼
AWS Lambda (Python 3.14 container)
        ├── SSM Parameter Store → Bluesky credentials
        ├── data/billionaires.json → random billionaire
        ├── data/charities.json   → random qualifying charity
        └── data/quotes.json      → random public-domain quote
        │
        ├── Pillow → renders quote as 1200×630 PNG
        └── AT Protocol API → post + image + threadgate (disable replies)
        │
        ▼
CloudWatch Logs (/aws/lambda/billionaire-matchmaker)
```

All AWS services stay within the free tier.

## Setup

### 1. Prerequisites

- AWS CLI configured
- Docker Desktop running
- OpenTofu (`brew install opentofu`)
- A Bluesky account for the bot (handle limit: 18 chars)

### 2. Bootstrap (one-time)

Creates the S3 state bucket, GitHub OIDC provider, and GitHub Actions IAM role.

```bash
cd tofu/modules/bootstrap
tofu init
# If GitHub OIDC provider already exists in your account, leave create_oidc_provider = false
tofu apply -var 'github_repo=YOUR_GITHUB_USERNAME/billionaire-matchmaker'
```

Add the output `github_actions_role_arn` as a GitHub Actions secret named `AWS_ROLE_ARN`.

### 3. Deploy

```bash
cp tofu/example.tfvars tofu/terraform.tfvars
./deploy.sh
```

`deploy.sh` creates the ECR repo, builds the Lambda container image (`--platform linux/amd64 --provenance=false`), pushes it, and runs `tofu apply`.

### 4. Set Bluesky credentials

Create an app password: **Settings → Privacy and Security → App Passwords**

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
# Offline smoke tests
pip install -r requirements-dev.txt
pytest tests/ -v

# Live invocation
aws lambda invoke \
  --function-name billionaire-matchmaker \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/out.json && cat /tmp/out.json
```

Or trigger via **GitHub Actions → post-now** (workflow_dispatch).

### 6. Apply bot label (one-time)

The Bluesky "bot" self-label isn't settable in the UI — apply it via the API:

```bash
python3 scripts/set_bot_label.py billionaire-match.bsky.social xxxx-xxxx-xxxx-xxxx
```

This marks the profile with a visible "Bot" badge and lets users filter it from their feeds.

## Posting cadence

Configure in `tofu/terraform.tfvars`, then redeploy:

```hcl
schedule_expression = "rate(1 day)"         # default
schedule_expression = "cron(0 15 * * ? *)"  # 3 PM UTC daily
```

## Data maintenance

All data is bundled as static JSON — no live scraping.

| File | Source | Update cadence |
|---|---|---|
| `lambda/data/billionaires.json` | Forbes Billionaires list | Annually |
| `lambda/data/charities.json` | ProPublica / IRS Form 990 | Annually |
| `lambda/data/quotes.json` | Pre-1928 public domain | As needed |

> **Note:** The ProPublica Nonprofit Explorer search API (`ntee[id]` filter) returns 500
> errors and omits revenue data from results. Charity data is pre-fetched and stored
> statically via the organization detail endpoint (`/api/v2/organizations/<ein>.json`).

## Skills demonstrated

| Skill | Implementation |
|---|---|
| IaC (OpenTofu) | Modular design — `bootstrap` + `bot` modules |
| Serverless | Lambda container image via ECR (not zip) |
| Event-driven | EventBridge Scheduler |
| Secrets management | SSM Parameter Store SecureString, least-privilege IAM |
| CI/CD | GitHub Actions with OIDC — no stored AWS credentials |
| Observability | Structured JSON logging to CloudWatch |
| Python | AT Protocol API, Pillow image generation, static data pipeline |
| Cost awareness | All services within AWS free tier |

## License

MIT — see [LICENSE](LICENSE). Quote and charity data attribution in [ATTRIBUTIONS](ATTRIBUTIONS).
