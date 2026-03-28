# LINE AI Secretary - Deployment Guide

## Prerequisites

- Google Cloud Platform project with billing enabled
- LINE Developers account with two channels:
  - **Messaging API** channel (for bot messaging)
  - **LINE Login** channel (for user authentication)
- Neon PostgreSQL database (https://neon.tech)
- Upstash Redis instance (https://upstash.com)
- Vercel account (https://vercel.com)
- GitHub repository connected to GCP and Vercel

## Architecture Overview

```
User <-> LINE App <-> LINE Platform <-> Cloud Run (Backend)
                                            |
                                    +-------+-------+
                                    |       |       |
                                  Neon   Upstash  Claude
                                  (PG)   (Redis)   (AI)

Admin <-> Vercel (Frontend) <-> Cloud Run (Backend)
```

## 1. Google Cloud Setup

### 1.1 Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com
```

### 1.2 Create Artifact Registry repository

```bash
gcloud artifacts repositories create line-ai-secretary \
  --repository-format=docker \
  --location=asia-northeast1
```

### 1.3 Create GCS bucket for file uploads

```bash
gcloud storage buckets create gs://line-ai-secretary-storage \
  --location=asia-northeast1
```

### 1.4 Store secrets in Secret Manager

```bash
# Store each secret (repeat for all)
echo -n "postgresql+asyncpg://user:pass@host/db" | \
  gcloud secrets create DATABASE_URL --data-file=-

echo -n "rediss://default:xxx@host:port" | \
  gcloud secrets create REDIS_URL --data-file=-

echo -n "sk-ant-xxx" | \
  gcloud secrets create ANTHROPIC_API_KEY --data-file=-

echo -n "your-channel-secret" | \
  gcloud secrets create LINE_CHANNEL_SECRET --data-file=-

echo -n "your-channel-token" | \
  gcloud secrets create LINE_CHANNEL_ACCESS_TOKEN --data-file=-

echo -n "your-login-channel-id" | \
  gcloud secrets create LINE_LOGIN_CHANNEL_ID --data-file=-

echo -n "your-login-channel-secret" | \
  gcloud secrets create LINE_LOGIN_CHANNEL_SECRET --data-file=-

# Generate encryption key: python -c "import secrets; print(secrets.token_hex(32))"
echo -n "your-encryption-key" | \
  gcloud secrets create ENCRYPTION_KEY --data-file=-

# Generate job auth secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
echo -n "your-job-auth-secret" | \
  gcloud secrets create JOB_AUTH_SECRET --data-file=-
```

### 1.5 Set up Workload Identity for GitHub Actions

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

SA_EMAIL="github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Allow GitHub repo to impersonate service account
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO"
```

## 2. Database Setup

### 2.1 Create Neon database

1. Create a project at https://console.neon.tech
2. Copy the connection string (use the pooled connection URL)
3. Store it in Secret Manager (see 1.4)

### 2.2 Run migrations

```bash
# Local
DATABASE_URL="postgresql+asyncpg://..." ./scripts/migrate.sh

# Or via Cloud Build (runs automatically on deploy)
```

## 3. Backend Deployment (Cloud Run)

### 3.1 Manual deployment

```bash
cd backend

# Build and push
IMAGE="asia-northeast1-docker.pkg.dev/YOUR_PROJECT/line-ai-secretary/backend"
docker build -t "$IMAGE:latest" .
docker push "$IMAGE:latest"

# Deploy
gcloud run deploy line-ai-secretary-api \
  --image="$IMAGE:latest" \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,LINE_CHANNEL_SECRET=LINE_CHANNEL_SECRET:latest,LINE_CHANNEL_ACCESS_TOKEN=LINE_CHANNEL_ACCESS_TOKEN:latest,LINE_LOGIN_CHANNEL_ID=LINE_LOGIN_CHANNEL_ID:latest,LINE_LOGIN_CHANNEL_SECRET=LINE_LOGIN_CHANNEL_SECRET:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest,JOB_AUTH_SECRET=JOB_AUTH_SECRET:latest" \
  --set-env-vars="FRONTEND_URL=https://your-app.vercel.app,GCS_BUCKET_NAME=line-ai-secretary-storage"
```

### 3.2 CI/CD deployment (recommended)

Push to `main` branch triggers automatic deployment via GitHub Actions.

Required GitHub Secrets:
- `GCP_WORKLOAD_IDENTITY_PROVIDER` - from step 1.5
- `GCP_SERVICE_ACCOUNT` - `github-deployer@PROJECT.iam.gserviceaccount.com`
- `GCP_PROJECT_ID` - your GCP project ID
- `FRONTEND_URL` - deployed frontend URL
- `GCS_BUCKET_NAME` - GCS bucket name

## 4. Frontend Deployment (Vercel)

### 4.1 Connect to Vercel

```bash
cd frontend
npx vercel link
```

### 4.2 Set environment variables in Vercel dashboard

- `VITE_API_URL` - Cloud Run backend URL (e.g., `https://line-ai-secretary-api-xxx.run.app`)
- `VITE_LINE_LOGIN_CHANNEL_ID` - LINE Login channel ID
- `VITE_LINE_LOGIN_REDIRECT_URI` - `https://your-app.vercel.app/callback`

### 4.3 CI/CD deployment

Required GitHub Secrets:
- `VERCEL_TOKEN` - from Vercel account settings
- `VERCEL_ORG_ID` - from `.vercel/project.json`
- `VERCEL_PROJECT_ID` - from `.vercel/project.json`

## 5. Cloud Scheduler Setup

After the backend is deployed, set up scheduled jobs:

```bash
./scripts/setup-scheduler.sh \
  https://line-ai-secretary-api-xxx.run.app \
  YOUR_PROJECT_ID
```

This creates three jobs:
| Job | Schedule | Description |
|-----|----------|-------------|
| morning-summary | Every 5 min (6-9 AM) | Morning briefing at each user's preferred time |
| event-reminders | Every 5 min | Upcoming event reminders |
| unreplied-reminders | Daily 18:00 JST | Unreplied message digest |

## 6. LINE Channel Configuration

### 6.1 Messaging API channel

1. Go to LINE Developers Console > your Messaging API channel
2. Set Webhook URL: `https://line-ai-secretary-api-xxx.run.app/api/line/webhook`
3. Enable "Use webhook"
4. Disable "Auto-reply messages" and "Greeting messages"

### 6.2 LINE Login channel

1. Go to LINE Developers Console > your LINE Login channel
2. Add callback URL: `https://your-app.vercel.app/callback`

## 7. Health Check Verification

```bash
# Simple health check
curl https://line-ai-secretary-api-xxx.run.app/api/health

# Detailed health check (DB, Redis, API keys)
curl https://line-ai-secretary-api-xxx.run.app/api/health/detailed
```

## Troubleshooting

### Cloud Run logs
```bash
gcloud run services logs read line-ai-secretary-api --region=asia-northeast1 --limit=50
```

### Container won't start
- Check PORT env var is set (Cloud Run injects it)
- Verify secrets are accessible: `gcloud secrets versions access latest --secret=SECRET_NAME`
- Check container locally: `docker run -p 8293:8293 -e PORT=8293 IMAGE`

### Database connection fails
- Ensure Neon DB allows connections from Cloud Run IPs (default: all IPs allowed)
- Check DATABASE_URL uses `postgresql+asyncpg://` scheme
- Verify SSL: append `?sslmode=require` to connection string

### LINE webhook not receiving events
- Verify webhook URL is correct in LINE console
- Check Cloud Run service allows unauthenticated access
- Ensure LINE_CHANNEL_SECRET matches the channel

### Cloud Scheduler jobs failing
- Check JOB_AUTH_SECRET matches between Secret Manager and scheduler headers
- Verify Cloud Run service URL is correct
- Check Cloud Scheduler service account has `roles/run.invoker` permission

### Frontend not connecting to backend
- Verify VITE_API_URL points to the Cloud Run URL
- Check CORS: FRONTEND_URL env var on backend must match the Vercel domain
- Ensure no trailing slash in URLs
