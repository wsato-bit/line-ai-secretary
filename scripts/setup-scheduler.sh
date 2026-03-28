#!/usr/bin/env bash
set -euo pipefail

# LINE AI Secretary - Cloud Scheduler Setup Script
# Usage: ./scripts/setup-scheduler.sh <BACKEND_URL> <PROJECT_ID> [REGION]

BACKEND_URL="${1:?Usage: $0 <BACKEND_URL> <PROJECT_ID> [REGION]}"
PROJECT_ID="${2:?Usage: $0 <BACKEND_URL> <PROJECT_ID> [REGION]}"
REGION="${3:-asia-northeast1}"

# Remove trailing slash from BACKEND_URL
BACKEND_URL="${BACKEND_URL%/}"

echo "=== LINE AI Secretary - Cloud Scheduler Setup ==="
echo "Backend URL: $BACKEND_URL"
echo "Project:     $PROJECT_ID"
echo "Region:      $REGION"
echo ""

# Retrieve JOB_AUTH_SECRET from Secret Manager
JOB_AUTH_SECRET=$(gcloud secrets versions access latest \
    --secret=JOB_AUTH_SECRET \
    --project="$PROJECT_ID" 2>/dev/null || true)

if [ -z "$JOB_AUTH_SECRET" ]; then
    echo "WARNING: Could not retrieve JOB_AUTH_SECRET from Secret Manager."
    echo "Please set it manually in the scheduler job headers."
    JOB_AUTH_SECRET="REPLACE_ME"
fi

create_or_update_job() {
    local JOB_NAME="$1"
    local SCHEDULE="$2"
    local ENDPOINT="$3"
    local TIMEZONE="${4:-Asia/Tokyo}"
    local DESCRIPTION="$5"

    echo "Setting up job: $JOB_NAME"
    echo "  Schedule: $SCHEDULE ($TIMEZONE)"
    echo "  Endpoint: $ENDPOINT"

    # Delete existing job if present
    gcloud scheduler jobs delete "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --quiet 2>/dev/null || true

    # Create job
    gcloud scheduler jobs create http "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="$SCHEDULE" \
        --time-zone="$TIMEZONE" \
        --uri="$BACKEND_URL$ENDPOINT" \
        --http-method=POST \
        --headers="Authorization=Bearer $JOB_AUTH_SECRET,Content-Type=application/json" \
        --description="$DESCRIPTION" \
        --attempt-deadline=300s \
        --max-retry-attempts=3

    echo "  -> Created."
    echo ""
}

# Morning summary - runs every 5 minutes, backend checks each user's preferred time
create_or_update_job \
    "morning-summary" \
    "*/5 6-9 * * *" \
    "/api/scheduler/morning-summary" \
    "Asia/Tokyo" \
    "Send morning briefing to users at their configured time"

# Event reminders - runs every 5 minutes to check upcoming events
create_or_update_job \
    "event-reminders" \
    "*/5 * * * *" \
    "/api/scheduler/event-reminders" \
    "Asia/Tokyo" \
    "Check and send reminders for upcoming calendar events"

# Unreplied message reminders - daily at 18:00 JST
create_or_update_job \
    "unreplied-reminders" \
    "0 18 * * *" \
    "/api/scheduler/unreplied-reminders" \
    "Asia/Tokyo" \
    "Send daily digest of unreplied messages"

echo "=== All scheduler jobs configured ==="
echo ""
echo "Verify with: gcloud scheduler jobs list --project=$PROJECT_ID --location=$REGION"
