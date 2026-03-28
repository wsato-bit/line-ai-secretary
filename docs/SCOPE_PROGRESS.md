# LINE AI Secretary — 進捗管理表

> 最終更新: 2026-03-28

---

## Phase 進捗サマリー

| Phase | 名称 | ステータス | 完了日 |
|-------|------|----------|--------|
| 1 | 要件定義 | [x] 完了 | 2026-03-28 |
| 2 | Git管理・リポジトリ設定 | [ ] 未着手 | - |
| 3 | フロントエンド基盤構築 | [ ] 未着手 | - |
| 4 | バックエンド基盤構築 | [ ] 未着手 | - |
| 5 | LINE Bot基盤（Webhook・認証） | [ ] 未着手 | - |
| 6 | AI秘書エージェント（Claude Tool Use） | [ ] 未着手 | - |
| 7 | スケジュール管理機能 | [ ] 未着手 | - |
| 8 | メール管理機能 | [ ] 未着手 | - |
| 9 | メモ管理機能 | [ ] 未着手 | - |
| 10 | LINE未返信管理機能 | [ ] 未着手 | - |
| 11 | リマインド・通知機能 | [ ] 未着手 | - |
| 12 | Web管理画面 | [ ] 未着手 | - |
| 13 | 管理者機能 | [ ] 未着手 | - |
| 14 | テスト・品質保証 | [ ] 未着手 | - |
| 15 | デプロイ | [ ] 未着手 | - |

---

## Phase 1: 要件定義 [x]

- [x] プロジェクト概要策定
- [x] 成果目標・KPI定義
- [x] ユーザーロール定義
- [x] ページ構成設計（5ページ）
- [x] 機能詳細仕様策定
- [x] データ設計概要（エンティティ定義）
- [x] AI設計（ツール定義15個、自律ループ仕様）
- [x] セキュリティ要件定義
- [x] 技術スタック選定
- [x] 外部API一覧整理
- [x] 業務フロー（AI代替マップ）作成
- [x] 要件定義書出力（docs/requirements.md）
- [x] CLAUDE.md作成

---

## Phase 2: Git管理・リポジトリ設定 [ ]

- [ ] GitHubリポジトリ作成（Private）
- [ ] ブランチ戦略設定（main / develop / feature/*）
- [ ] .gitignore設定
- [ ] GitHub Actions CI/CD設定（ci.yml）
- [ ] ブランチ保護ルール設定

---

## Phase 3: フロントエンド基盤構築 [ ]

- [ ] Vite + React + TypeScriptプロジェクト初期化
- [ ] MUI v6 セットアップ
- [ ] React Router v6 ルーティング設定（5ページ）
- [ ] Zustand ストアセットアップ
- [ ] React Query セットアップ
- [ ] 環境変数設定（config/index.ts）
- [ ] 型定義ファイル作成（types/index.ts）
- [ ] ESLint / Prettier 設定
- [ ] レイアウトコンポーネント（ヘッダー・ナビゲーション）
- [ ] 認証ガード（LINE Login状態チェック）

---

## Phase 4: バックエンド基盤構築 [ ]

- [ ] FastAPIプロジェクト初期化
- [ ] ディレクトリ構成作成
- [ ] PostgreSQL（Neon）接続設定
- [ ] SQLAlchemy + Alembic セットアップ
- [ ] Redis（Upstash）接続設定
- [ ] 環境変数設定（config/index.py）
- [ ] 型定義ファイル作成（types/index.py）
- [ ] DBモデル定義（User, Memo, MemoCategory, EmailFilter, UnrepliedItem, EventColorRule, NotificationSetting, EditHistory, AuditLog, OAuthToken）
- [ ] 初期マイグレーション作成・実行
- [ ] ヘルスチェックエンドポイント（/api/health）
- [ ] グレースフルシャットダウン実装
- [ ] CORS設定
- [ ] エラーハンドリング共通化
- [ ] 監査ログミドルウェア
- [ ] flake8 / black 設定

---

## Phase 5: LINE Bot基盤（Webhook・認証） [ ]

- [ ] LINE Messaging API チャネル設定
- [ ] LINE Login チャネル設定
- [ ] Webhook受信エンドポイント実装
- [ ] X-Line-Signature 署名検証
- [ ] LINE Login OAuth 2.0フロー実装
- [ ] ユーザー登録フロー（友だち追加→利用申請→承認待ち）
- [ ] LINE リッチメニュー設定（6分割）
- [ ] Reply / Push メッセージ送信ユーティリティ
- [ ] Flex Message テンプレート作成

---

## Phase 6: AI秘書エージェント（Claude Tool Use） [ ]

- [ ] Anthropic SDK セットアップ
- [ ] システムプロンプト設計
- [ ] ツール定義（15ツール）JSON Schema作成
- [ ] 自律ループエンジン実装（max_turns=10）
- [ ] ツールディスパッチャー実装
- [ ] 並列ツール実行対応
- [ ] 承認要求フロー実装（approval_request）
- [ ] ショートカットワード判定ロジック
- [ ] LINE→エージェント→LINE 応答フロー
- [ ] Web SSEストリーミング実装
- [ ] エラーハンドリング・リトライ

---

## Phase 7: スケジュール管理機能 [ ]

- [ ] Google Calendar API OAuth 2.0 連携
- [ ] get_schedule ツール実装
- [ ] find_available_slots ツール実装
- [ ] create_event ツール実装（色分け自動設定含む）
- [ ] update_event ツール実装
- [ ] delete_event ツール実装
- [ ] EventColorRule デフォルト初期データ
- [ ] FreeBusy API活用
- [ ] LINE向け予定表示フォーマット

---

## Phase 8: メール管理機能 [ ]

- [ ] Gmail API OAuth 2.0 連携
- [ ] get_emails ツール実装
- [ ] AI自動分類ロジック（重要/参考/除外）
- [ ] 自動除外判定（List-Unsubscribe、ドメイン、件名パターン）
- [ ] メール要約生成
- [ ] send_email_reply ツール実装（承認フロー付き）
- [ ] set_email_filter ツール実装
- [ ] EmailFilter CRUD API
- [ ] LINE向けメール要約フォーマット

---

## Phase 9: メモ管理機能 [ ]

- [ ] Google Cloud Storage セットアップ
- [ ] Google Cloud Vision API セットアップ
- [ ] save_memo ツール実装
- [ ] AI自動分類・カテゴリ付け・タグ付けロジック
- [ ] 画像アップロード → GCS保存 → OCRテキスト抽出
- [ ] URL送信 → メタデータ取得 → AI要約
- [ ] search_memo ツール実装（全文検索）
- [ ] delete_memo ツール実装（論理削除）
- [ ] MemoCategory CRUD API
- [ ] デフォルトカテゴリ初期データ
- [ ] LINE向けメモ表示フォーマット

---

## Phase 10: LINE未返信管理機能 [ ]

- [ ] register_unreplied ツール実装
- [ ] list_unreplied ツール実装（経過日数計算）
- [ ] complete_unreplied ツール実装
- [ ] LINE向け未返信リスト表示フォーマット

---

## Phase 11: リマインド・通知機能 [ ]

- [ ] Cloud Scheduler セットアップ
- [ ] Cloud Tasks セットアップ
- [ ] 朝サマリー定期実行（get_schedule → Push通知）
- [ ] 予定前リマインド通知（スケジューラ監視）
- [ ] 予定ごとの個別リマインド設定
- [ ] 未返信リマインド定期実行（list_unreplied → 閾値判定 → Push通知）
- [ ] NotificationSetting 反映ロジック

---

## Phase 12: Web管理画面 [ ]

- [ ] P-001: ログインページ実装
  - [ ] LINE Loginボタン
  - [ ] 利用申請フォーム
  - [ ] 承認待ちステータス表示
- [ ] P-002: ワークスペースページ実装
  - [ ] 今日の予定セクション
  - [ ] 未読重要メール要約セクション
  - [ ] LINE未返信リストセクション
  - [ ] 最近のメモセクション
  - [ ] 各項目からの操作機能
- [ ] P-003: メモ管理ページ実装
  - [ ] カテゴリ別タブ/フィルタ
  - [ ] 全文検索バー
  - [ ] メモカード表示（テキスト/画像/URL）
  - [ ] タグ編集（インライン）
  - [ ] カテゴリ管理
  - [ ] エクスポート機能
- [ ] P-004: 設定ページ実装
  - [ ] 通知時間設定
  - [ ] リマインド間隔設定
  - [ ] Gmail連携（OAuth）
  - [ ] Googleカレンダー連携（OAuth）
  - [ ] カレンダー色分けルール設定
  - [ ] メールフィルタ設定

---

## Phase 13: 管理者機能 [ ]

- [ ] A-001: ユーザー管理ページ実装
  - [ ] 利用申請一覧
  - [ ] 承認/却下アクション
  - [ ] 登録ユーザー一覧
  - [ ] ユーザー詳細表示
  - [ ] ユーザー無効化/再有効化
- [ ] approve_user ツール実装
- [ ] 管理者権限チェックミドルウェア

---

## Phase 14: テスト・品質保証 [ ]

- [ ] バックエンド単体テスト（pytest）
- [ ] API統合テスト
- [ ] フロントエンド単体テスト（Vitest）
- [ ] E2Eテスト（Playwright）
- [ ] LINE Webhookテスト（モック）
- [ ] AI エージェントテスト（ツール実行フロー）
- [ ] セキュリティテスト（署名検証、認可チェック）
- [ ] パフォーマンステスト

---

## Phase 15: デプロイ [ ]

- [ ] Vercel フロントエンドデプロイ設定
- [ ] Google Cloud Run バックエンドデプロイ設定
- [ ] Neon PostgreSQL 本番環境設定
- [ ] Upstash Redis 本番環境設定
- [ ] 環境変数設定（本番）
- [ ] ドメイン設定・SSL証明書
- [ ] Cloud Scheduler / Cloud Tasks 本番設定
- [ ] 監視・アラート設定
- [ ] 本番動作確認

---

## ページ管理表

| ID | ページ名 | ルート | 権限 | Phase | ステータス |
|----|---------|-------|------|-------|----------|
| P-001 | ログイン | /login | 全員 | Phase 12 | [ ] 未着手 |
| P-002 | ワークスペース | / | ユーザー | Phase 12 | [ ] 未着手 |
| P-003 | メモ管理 | /memos | ユーザー | Phase 12 | [ ] 未着手 |
| P-004 | 設定 | /settings | ユーザー | Phase 12 | [ ] 未着手 |
| A-001 | ユーザー管理 | /admin/users | 管理者 | Phase 13 | [ ] 未着手 |

---

## ツール管理表

| # | ツール名 | カテゴリ | Phase | ステータス |
|---|---------|---------|-------|----------|
| 1 | get_schedule | スケジュール | Phase 7 | [ ] 未着手 |
| 2 | find_available_slots | スケジュール | Phase 7 | [ ] 未着手 |
| 3 | create_event | スケジュール | Phase 7 | [ ] 未着手 |
| 4 | update_event | スケジュール | Phase 7 | [ ] 未着手 |
| 5 | delete_event | スケジュール | Phase 7 | [ ] 未着手 |
| 6 | get_emails | メール | Phase 8 | [ ] 未着手 |
| 7 | send_email_reply | メール | Phase 8 | [ ] 未着手 |
| 8 | set_email_filter | メール | Phase 8 | [ ] 未着手 |
| 9 | save_memo | メモ | Phase 9 | [ ] 未着手 |
| 10 | search_memo | メモ | Phase 9 | [ ] 未着手 |
| 11 | delete_memo | メモ | Phase 9 | [ ] 未着手 |
| 12 | register_unreplied | 未返信 | Phase 10 | [ ] 未着手 |
| 13 | list_unreplied | 未返信 | Phase 10 | [ ] 未着手 |
| 14 | complete_unreplied | 未返信 | Phase 10 | [ ] 未着手 |
| 15 | approve_user | 管理 | Phase 13 | [ ] 未着手 |

---

## 外部API連携管理表

| API名 | Phase | ステータス |
|-------|-------|----------|
| LINE Messaging API | Phase 5 | [ ] 未着手 |
| LINE Login API | Phase 5 | [ ] 未着手 |
| Gmail API | Phase 8 | [ ] 未着手 |
| Google Calendar API | Phase 7 | [ ] 未着手 |
| Anthropic Claude API | Phase 6 | [ ] 未着手 |
| Google Cloud Storage | Phase 9 | [ ] 未着手 |
| Google Cloud Vision API | Phase 9 | [ ] 未着手 |
