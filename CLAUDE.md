# billionaire-matchmaker

Bluesky bot that matches a random US billionaire's net worth against a random US charity,
showing how many years that fortune would fund the charity, plus a public-domain anti-greed quote.

## Stack

- **Runtime**: Python 3.14 Lambda container image (via ECR)
- **IaC**: OpenTofu (`tofu/`)
- **Scheduler**: EventBridge Scheduler → Lambda
- **Secrets**: SSM Parameter Store SecureString
- **CI**: GitHub Actions (OIDC, no stored creds)

## Layout

```
lambda/          Python app code + bundled data
tofu/            OpenTofu root + modules
  modules/
    bootstrap/   One-time: S3 state bucket + GitHub OIDC
    bot/         Lambda, ECR, EventBridge, SSM, CloudWatch, IAM
Dockerfile       Lambda container image
deploy.sh        Local build + deploy
```

## Common commands

```bash
# Bootstrap (one-time, run before first tofu apply)
cd tofu/modules/bootstrap && tofu init && tofu apply

# Build image + deploy infrastructure
./deploy.sh

# Invoke Lambda immediately
aws lambda invoke --function-name billionaire-matchmaker /tmp/out.json && cat /tmp/out.json

# Tail Lambda logs
aws logs tail /aws/lambda/billionaire-matchmaker --follow
```

## Data files

- `lambda/data/billionaires.json` — curated Forbes snapshot (~100 US billionaires, 2025)
- `lambda/data/quotes.json` — public-domain anti-greed quotes (pre-1928 authors or federal works)

Update billionaires.json annually after Forbes releases its list. Net worths are intentionally
snapshot values, not live-scraped — stable and reproducible.

## Secrets setup (before first post)

After deploying infrastructure, overwrite the placeholder SSM values:

```bash
aws ssm put-parameter --name /billionaire-matchmaker/bluesky-handle \
  --value "yourbot.bsky.social" --type SecureString --overwrite

aws ssm put-parameter --name /billionaire-matchmaker/bluesky-app-password \
  --value "xxxx-xxxx-xxxx-xxxx" --type SecureString --overwrite
```

Create the Bluesky app password at: Settings → Privacy and Security → App Passwords

## Post format

```
[Name] has a net worth of $[X]B as of [year] (source: Forbes).

That's [Y] years of funding for [Charity Name] ($[Z]M/yr budget).

"[Quote]" — [Author]

#eattherich
```

Posts are capped at 300 graphemes (Bluesky limit). Quotes are truncated with "…" if needed.
Charity name is hyperlinked to ProPublica. Billionaire name is hyperlinked to Forbes profile.

## Design constraints

- All AWS services stay within free tier
- No live scraping — billionaire data is a static JSON snapshot updated manually
- Lambda runs as container image (not zip) to showcase ECR/Docker skills
- EventBridge schedule is configurable via tfvar (`schedule_expression`)
