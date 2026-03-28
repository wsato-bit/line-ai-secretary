#!/usr/bin/env bash
set -euo pipefail

# LINE AI Secretary - Database Migration Script
# Usage: ./scripts/migrate.sh [upgrade|downgrade] [revision]
#   Default: upgrade head

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

ACTION="${1:-upgrade}"
REVISION="${2:-head}"

echo "=== LINE AI Secretary DB Migration ==="
echo "Action:   $ACTION"
echo "Revision: $REVISION"
echo ""

# Check DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    if [ -f "$BACKEND_DIR/.env.local" ]; then
        echo "Loading .env.local..."
        export $(grep -v '^#' "$BACKEND_DIR/.env.local" | xargs)
    else
        echo "ERROR: DATABASE_URL is not set and .env.local not found."
        exit 1
    fi
fi

cd "$BACKEND_DIR"

echo "Running: alembic $ACTION $REVISION"
alembic "$ACTION" "$REVISION"

echo ""
echo "Migration completed successfully."
