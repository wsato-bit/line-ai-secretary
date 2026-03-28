#!/bin/bash
set -euo pipefail

# Neon PostgreSQL セットアップスクリプト
# 前提: neonctl がインストール済み (npm i -g neonctl)

echo "=== Neon PostgreSQL セットアップ ==="

PROJECT_NAME="line-ai-secretary"
BRANCH_NAME="main"
DB_NAME="line_ai_secretary"

echo "1. プロジェクト作成..."
neonctl projects create --name "$PROJECT_NAME" --output json > /tmp/neon-project.json
PROJECT_ID=$(jq -r '.project.id' /tmp/neon-project.json)
echo "   Project ID: $PROJECT_ID"

echo "2. データベース作成..."
neonctl databases create --project-id "$PROJECT_ID" --branch "$BRANCH_NAME" --name "$DB_NAME"

echo "3. 接続文字列取得..."
CONNECTION_STRING=$(neonctl connection-string --project-id "$PROJECT_ID" --branch "$BRANCH_NAME" --database-name "$DB_NAME")
echo "   DATABASE_URL=$CONNECTION_STRING"

echo ""
echo "=== 完了 ==="
echo ""
echo "次のステップ:"
echo "  1. backend/.env.local に DATABASE_URL を設定"
echo "     DATABASE_URL=$CONNECTION_STRING"
echo ""
echo "  2. マイグレーション実行"
echo "     cd backend && alembic upgrade head"
echo ""
echo "  3. GCP Secret Manager に登録"
echo "     gcloud secrets create DATABASE_URL --data-file=- <<< '$CONNECTION_STRING'"
