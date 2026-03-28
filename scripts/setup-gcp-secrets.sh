#!/bin/bash
set -euo pipefail

# GCP Secret Manager 一括登録スクリプト
# 前提: gcloud CLI がインストール・認証済み、.env.local に値が設定済み

echo "=== GCP Secret Manager セットアップ ==="

PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_IDを環境変数に設定してください}"
REGION="asia-northeast1"

# Secret Manager API 有効化
echo "1. Secret Manager API 有効化..."
gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"

# backend/.env.local から読み込み
ENV_FILE="$(dirname "$0")/../backend/.env.local"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE が見つかりません。先に環境変数を設定してください。"
    exit 1
fi

echo "2. シークレット登録..."

# 登録するシークレット一覧
SECRETS=(
    "DATABASE_URL"
    "REDIS_URL"
    "ANTHROPIC_API_KEY"
    "LINE_CHANNEL_SECRET"
    "LINE_CHANNEL_ACCESS_TOKEN"
    "LINE_LOGIN_CHANNEL_ID"
    "LINE_LOGIN_CHANNEL_SECRET"
    "ENCRYPTION_KEY"
    "JOB_AUTH_SECRET"
)

for SECRET_NAME in "${SECRETS[@]}"; do
    # .env.local から値を取得
    VALUE=$(grep "^${SECRET_NAME}=" "$ENV_FILE" | cut -d'=' -f2-)

    if [ -z "$VALUE" ]; then
        echo "   SKIP: $SECRET_NAME (値が未設定)"
        continue
    fi

    # シークレットが既に存在するか確認
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        echo "   UPDATE: $SECRET_NAME"
        echo -n "$VALUE" | gcloud secrets versions add "$SECRET_NAME" --project="$PROJECT_ID" --data-file=-
    else
        echo "   CREATE: $SECRET_NAME"
        echo -n "$VALUE" | gcloud secrets create "$SECRET_NAME" --project="$PROJECT_ID" --data-file=- --replication-policy="user-managed" --locations="$REGION"
    fi
done

echo ""
echo "3. Cloud Run サービスアカウントにアクセス権付与..."
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"
for SECRET_NAME in "${SECRETS[@]}"; do
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
        --project="$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet 2>/dev/null || true
done

echo ""
echo "=== 完了 ==="
echo "Secret Manager に ${#SECRETS[@]} 個のシークレットを登録しました。"
