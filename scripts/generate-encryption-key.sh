#!/bin/bash
set -euo pipefail

# AES-256暗号化キーとジョブ認証シークレットの生成

echo "=== セキュリティキー生成 ==="
echo ""

# Fernet key (base64-encoded 32 bytes)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo ""

# Job auth secret
JOB_AUTH_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "JOB_AUTH_SECRET=$JOB_AUTH_SECRET"
echo ""

echo "────────────────────────────────────"
echo "これらを backend/.env.local に追加してください:"
echo ""
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "JOB_AUTH_SECRET=$JOB_AUTH_SECRET"
