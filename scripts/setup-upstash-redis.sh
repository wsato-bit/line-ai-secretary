#!/bin/bash
set -euo pipefail

# Upstash Redis セットアップスクリプト
# 前提: upstash CLI がインストール済み、またはダッシュボードから手動設定

echo "=== Upstash Redis セットアップ ==="
echo ""
echo "Upstash Redis はダッシュボードから作成してください:"
echo "  https://console.upstash.com/"
echo ""
echo "設定手順:"
echo "  1. 新しいデータベースを作成"
echo "     - Name: line-ai-secretary"
echo "     - Region: ap-northeast-1 (Tokyo)"
echo "     - Type: Regional"
echo ""
echo "  2. 接続情報をコピー"
echo "     - REDIS_URL (redis://default:xxx@xxx.upstash.io:6379)"
echo ""
echo "  3. backend/.env.local に設定"
echo "     REDIS_URL=redis://default:xxx@xxx.upstash.io:6379"
echo ""
echo "  4. GCP Secret Manager に登録"
echo "     gcloud secrets create REDIS_URL --data-file=- <<< 'REDIS_URL_VALUE'"
