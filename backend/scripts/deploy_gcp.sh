#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# scripts/deploy_gcp.sh — Phase 9: Deploy to GCP Cloud Run
#
# Usage:
#   chmod +x scripts/deploy_gcp.sh
#   ./scripts/deploy_gcp.sh
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. GCP project created
#   3. APIs enabled: Cloud Run, Container Registry, Secret Manager
#   4. Secrets stored in Secret Manager (see README)
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="codereview-agent"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying CodeReview AI Agent to GCP Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region:  ${REGION}"
echo "   Image:   ${IMAGE}"
echo ""

# ── Step 1: Enable required APIs ─────────────────────────────────
echo "1/5 Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  --project="${PROJECT_ID}"

# ── Step 2: Store secrets in Secret Manager ───────────────────────
echo ""
echo "2/5 Storing secrets in Secret Manager..."
echo "   (Skip if already done)"

# Store each secret (prompts for values):
# gcloud secrets create GROQ_API_KEY --data-file=- --project="${PROJECT_ID}"
# gcloud secrets create GITHUB_TOKEN --data-file=- --project="${PROJECT_ID}"
# gcloud secrets create GITHUB_WEBHOOK_SECRET --data-file=- --project="${PROJECT_ID}"
# gcloud secrets create DATABASE_URL --data-file=- --project="${PROJECT_ID}"

# ── Step 3: Build and push Docker image ───────────────────────────
echo ""
echo "3/5 Building and pushing Docker image..."
cd "$(dirname "$0")/../backend"
gcloud builds submit \
  --tag="${IMAGE}" \
  --project="${PROJECT_ID}"

# ── Step 4: Deploy to Cloud Run ──────────────────────────────────
echo ""
echo "4/5 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=10 \
  --set-secrets="GROQ_API_KEY=GROQ_API_KEY:latest,GITHUB_TOKEN=GITHUB_TOKEN:latest,GITHUB_WEBHOOK_SECRET=GITHUB_WEBHOOK_SECRET:latest,DATABASE_URL=DATABASE_URL:latest" \
  --set-env-vars="APP_ENV=production,GROQ_MODEL=llama-3.1-70b-versatile"

# ── Step 5: Get the service URL ───────────────────────────────────
echo ""
echo "5/5 Getting service URL..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎉 PHASE 9 DEPLOYMENT COMPLETE!"
echo ""
echo "   Service URL: ${SERVICE_URL}"
echo "   Health:      ${SERVICE_URL}/health"
echo "   Webhook URL: ${SERVICE_URL}/webhook"
echo ""
echo "   Next: Add ${SERVICE_URL}/webhook as your GitHub webhook"
echo "═══════════════════════════════════════════════════════════"
