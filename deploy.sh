#!/usr/bin/env bash
set -euo pipefail

# ── Preflight ─────────────────────────────────────────────────────────────────

if ! docker info &>/dev/null; then
  echo "ERROR: Docker daemon is not running." >&2
  exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
  echo "ERROR: AWS credentials not configured." >&2
  exit 1
fi

REGION=$(aws configure get region 2>/dev/null || echo "us-west-2")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
REPO_NAME="billionaire-matchmaker"
GIT_SHA=$(git rev-parse --short HEAD)
IMAGE_URI="${ECR_REGISTRY}/${REPO_NAME}:${GIT_SHA}"

echo "==> Region:   ${REGION}"
echo "==> Account:  ${ACCOUNT_ID}"
echo "==> Image:    ${IMAGE_URI}"
echo ""

# ── Ensure ECR repo exists (tofu apply -target) ───────────────────────────────

echo "==> Ensuring ECR repository exists..."
(cd tofu && tofu init -input=false && \
  tofu apply -auto-approve -input=false \
    -target=module.bot.aws_ecr_repository.bot \
    -target=module.bot.aws_ecr_lifecycle_policy.bot \
    -var "image_uri=placeholder")

# ── Build and push image ──────────────────────────────────────────────────────

echo "==> Logging in to ECR..."
aws ecr get-login-password --region "${REGION}" | \
  docker login --username AWS --password-stdin "${ECR_REGISTRY}"

echo "==> Building image..."
docker build --platform linux/amd64 --provenance=false -t "${IMAGE_URI}" .

echo "==> Pushing image..."
docker push "${IMAGE_URI}"

# ── Full tofu apply ───────────────────────────────────────────────────────────

echo "==> Deploying infrastructure..."
(cd tofu && tofu apply -auto-approve -input=false -var "image_uri=${IMAGE_URI}")

echo ""
echo "Done. Lambda function: ${REPO_NAME}"
echo "To post immediately: aws lambda invoke --function-name ${REPO_NAME} --payload '{}' --cli-binary-format raw-in-base64-out /tmp/out.json && cat /tmp/out.json"
