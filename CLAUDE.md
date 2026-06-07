# billionaire-matchmaker

Bluesky bot that matches a random US billionaire's net worth against a random US charity,
showing how many years that fortune would fund the charity, plus a public-domain anti-greed
quote rendered as an attached image.

## Stack

- **Runtime**: Python 3.14 Lambda container image (via ECR)
- **IaC**: OpenTofu (`tofu/`)
- **Scheduler**: EventBridge Scheduler → Lambda (daily, ~03:18 UTC)
- **Secrets**: SSM Parameter Store SecureString
- **Dedup**: DynamoDB (PAY_PER_REQUEST) — tracks recent pairings, 30-day TTL
- **CI**: GitHub Actions (OIDC, no stored creds)

## Layout

```
lambda/          Python app code + bundled data
  data/
    billionaires.json   Forbes 2025 snapshot (~100 US billionaires)
    charities.json      34 curated US nonprofits with IRS 990 revenue data
    quotes.json         91 public-domain anti-greed quotes
tofu/            OpenTofu root + modules
  modules/
    bootstrap/   One-time: S3 state bucket + GitHub OIDC
    bot/         Lambda, ECR, EventBridge, SSM, DynamoDB, CloudWatch, IAM
tests/           Offline smoke tests (pytest)
Dockerfile       Lambda container image
deploy.sh        Local build + deploy
```

## Before pushing

Run the security review and smoke tests before any `git push`:

```bash
/security-review   # Claude Code skill — reviews staged changes for vulnerabilities
pytest tests/ -v   # offline smoke tests
```

## Common commands

```bash
# Run smoke tests before deploying
pip install -r requirements-dev.txt
pytest tests/ -v

# Bootstrap (one-time, run before first tofu apply)
cd tofu/modules/bootstrap && tofu init && tofu apply

# Build image + deploy infrastructure
./deploy.sh

# Invoke Lambda immediately
aws lambda invoke --function-name billionaire-matchmaker \
  --payload '{}' --cli-binary-format raw-in-base64-out \
  /tmp/out.json && cat /tmp/out.json

# Tail Lambda logs
aws logs tail /aws/lambda/billionaire-matchmaker --follow
```

## Data files

- `lambda/data/billionaires.json` — curated Forbes snapshot (~100 US billionaires, 2025).
  Update annually after Forbes releases its list. Net worths are intentionally snapshot
  values, not live-scraped.
- `lambda/data/charities.json` — 34 curated US nonprofits with annual revenue from IRS 990
  filings via ProPublica. Update annually. Do NOT use the ProPublica search API at runtime —
  the `ntee[id]` filter returns 500 and the search endpoint omits revenue data entirely.
- `lambda/data/quotes.json` — 91 public-domain anti-greed quotes (pre-1928 authors or
  federal government works).

## Secrets setup (before first post)

After deploying infrastructure, overwrite the placeholder SSM values:

```bash
aws ssm put-parameter --name /billionaire-matchmaker/bluesky-handle \
  --value "billionaire-match.bsky.social" --type SecureString --overwrite

aws ssm put-parameter --name /billionaire-matchmaker/bluesky-app-password \
  --value "xxxx-xxxx-xxxx-xxxx" --type SecureString --overwrite
```

Create the Bluesky app password at: Settings → Privacy and Security → App Passwords

## Bot label (one-time, after first deploy)

The Bluesky "bot" self-label cannot be set in the UI — apply it via:

```bash
python3 scripts/set_bot_label.py billionaire-match.bsky.social xxxx-xxxx-xxxx-xxxx
```

## Post format

```
[Name] has a net worth of $[X]B as of [year] (source: Forbes).

That's [Y] years of funding for [Charity Name] ($[Z]M/yr budget, [year] data).

#eattherich
```

- Post text is capped at 300 graphemes (Bluesky limit).
- Billionaire name is hyperlinked to their Forbes profile.
- Charity name is hyperlinked to their ProPublica page.
- Quote is rendered as a 1200×630 PNG image (dark navy, DejaVu fonts) and attached to the post.
- Replies are disabled via a threadgate record (same rkey as the post).

## Design constraints

- All AWS services stay within free tier
- No live scraping — all data is static JSON updated manually
- Lambda runs as container image (not zip) to showcase ECR/Docker skills
- EventBridge schedule is configurable via tfvar (`schedule_expression`)
- Docker image must be built with `--platform linux/amd64 --provenance=false`
  (`--provenance=false` prevents OCI manifest format that Lambda rejects)
- Pillow requires `freetype-devel` at image build time (no pre-built wheel for Python 3.14)
