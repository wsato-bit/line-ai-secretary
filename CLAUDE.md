# CLAUDE.md - LINE AI Secretary

## プロジェクト概要

LINEをメインインターフェースとして、Gmail・Googleカレンダー・多目的メモ・LINE未返信リマインドを一元管理するAI個人秘書サービス。
Claude Tool Useによる自律エージェントが対話形式でタスクを実行。
初期は個人利用、将来マルチユーザー展開（承認制）。

### アーキテクチャ
- オーケストレータ: Claude Sonnet 4.5（Tool Use自律ループ、max_turns=10）
- LINE通信: Webhook / Reply / Push
- Web通信: SSEストリーミング
- AI制御: Claude Tool Useによる自律ツール選択

## 技術スタック

```yaml
frontend: React 18 + TypeScript 5 + MUI v6
  bundler: Vite 5
  routing: React Router v6
  state: Zustand
  api: React Query
  deploy: Vercel

backend: Python 3.12+ + FastAPI
  ai: Anthropic SDK（直接）
  google: Google API Client Library
  line: LINE Bot SDK for Python
  deploy: Google Cloud Run

database: PostgreSQL (Neon)
cache: Redis (Upstash)
storage: Google Cloud Storage
ocr: Google Cloud Vision API
auth: LINE Login (OAuth 2.0)
scheduler: Cloud Scheduler + Cloud Tasks
```

## ポート設定

```yaml
frontend: 3847
backend: 8293
```

## 環境変数

```yaml
frontend: frontend/.env.local
  - VITE_API_URL
  - VITE_LINE_LOGIN_CHANNEL_ID
  - VITE_LINE_LOGIN_REDIRECT_URI
  設定モジュール: src/config/index.ts（import.meta.env集約）

backend: backend/.env.local
  - DATABASE_URL
  - REDIS_URL
  - ANTHROPIC_API_KEY
  - LINE_CHANNEL_SECRET
  - LINE_CHANNEL_ACCESS_TOKEN
  - LINE_LOGIN_CHANNEL_ID
  - LINE_LOGIN_CHANNEL_SECRET
  - GOOGLE_APPLICATION_CREDENTIALS
  - GCS_BUCKET_NAME
  - ENCRYPTION_KEY（AES-256用）
  設定モジュール: src/config/index.py（os.environ集約）

ハードコード禁止: 環境変数はconfig経由のみ
絶対禁止: .env, .env.local をリポジトリにコミットしない
```

## 命名規則

```yaml
フロントエンド:
  ファイル: PascalCase.tsx（コンポーネント）/ camelCase.ts（その他）
  変数/関数: camelCase
  定数: UPPER_SNAKE_CASE
  型: PascalCase
  型定義: frontend/src/types/index.ts（単一真実源）

バックエンド:
  ファイル: snake_case.py
  変数/関数: snake_case
  定数: UPPER_SNAKE_CASE
  クラス: PascalCase
  型定義: backend/src/types/index.py
```

## コード品質

```yaml
関数行数: 100行以下
ファイル行数: 700行以下
複雑度: 10以下
行長: 120文字
```

## AI API利用ルール

```yaml
エージェントオーケストレータ: Claude Sonnet 4.5 (Tool Use)
  - 全対話・判断・ツール選択を自律実行
  - max_turns: 10

ツール: 15ツール（スケジュール5, メール3, メモ3, 未返信3, 管理1）

通信方式:
  LINE: Webhook → Reply/Push
  Web: SSE（text, tool_start, tool_end, approval_request, error, done）

全APIでユーザーデータの学習利用をopt-out設定すること
```

## セキュリティ必須事項

```yaml
- 全通信HTTPS (TLS 1.3)
- LINE Webhook署名検証（X-Line-Signature）
- 保存データAES-256暗号化（OAuthトークン等）
- LINE Login (OAuth 2.0) による統一認証
- CSRF対策: トークン必須（Web管理画面）
- 入力値サニタイゼーション: 全エンドポイント
- ユーザー間データ完全分離（クエリにuser_idフィルタ必須）
- 監査ログ: 全操作記録
- AI API opt-out: ユーザーデータを学習に使用しない
```

## ディレクトリ構成

```
/
├── frontend/
│   ├── src/
│   │   ├── components/    # UIコンポーネント
│   │   ├── pages/         # ページコンポーネント（5ページ）
│   │   ├── hooks/         # カスタムフック
│   │   ├── stores/        # Zustandストア
│   │   ├── services/      # API呼出し
│   │   ├── types/         # 型定義（単一真実源）
│   │   ├── config/        # 環境変数集約
│   │   └── utils/         # ユーティリティ
│   ├── public/
│   └── .env.local
├── backend/
│   ├── src/
│   │   ├── api/           # APIエンドポイント
│   │   ├── services/      # ビジネスロジック
│   │   ├── models/        # DBモデル
│   │   ├── ai/            # エージェントオーケストレータ
│   │   │   └── tools/     # Tool Use ツール実装（15ツール）
│   │   ├── rag/           # RAG
│   │   ├── types/         # 型定義
│   │   ├── config/        # 環境変数集約
│   │   └── utils/         # ユーティリティ
│   ├── alembic/           # DBマイグレーション
│   └── .env.local
├── docs/
│   ├── requirements.md    # 要件定義書
│   └── SCOPE_PROGRESS.md  # 進捗管理表
├── .github/
│   └── workflows/
│       └── ci.yml         # CI/CDパイプライン
└── CLAUDE.md              # このファイル
```

## CI/CD設定

### GitHub Actions（PR時に自動実行）
| チェック | 対象 | コマンド |
|---------|------|---------|
| TypeScript | frontend | `npx tsc --noEmit` |
| Lint (JS/TS) | frontend | `npm run lint` |
| Build | frontend | `npm run build` |
| Lint (Python) | backend | `flake8 --max-line-length=120` |
| Format (Python) | backend | `black --check --line-length=120` |

### ブランチ戦略
- `main`: 本番環境
- `develop`: 開発統合ブランチ
- `feature/*`: 機能開発ブランチ

### ページ構成（5ページ）
| ID | ページ名 | ルート | 権限 |
|----|---------|-------|------|
| P-001 | ログイン | /login | 全員 |
| P-002 | ワークスペース | / | ユーザー |
| P-003 | メモ管理 | /memos | ユーザー |
| P-004 | 設定 | /settings | ユーザー |
| A-001 | ユーザー管理 | /admin/users | 管理者 |
