# LINE AI Secretary — 要件定義書

> 最終更新: 2026-03-28
> ステータス: Phase 1 完了

---

## 1. プロジェクト概要

### 1.1 サービス概要

LINE AI Secretary は、LINEを唯一のメインインターフェースとして、Gmail・Googleカレンダー・多目的メモ・LINE未返信リマインドを一元管理するAI個人秘書サービスである。

- 初期は個人利用、将来マルチユーザー展開（承認制）
- Web管理画面はLINEで扱いにくい一覧性・編集・設定を補完する役割

### 1.2 成果目標

| # | 指標 | 目標値 |
|---|------|--------|
| 1 | メール確認・返信の所要時間 | 従来比50%削減 |
| 2 | スケジュール登録 | 3タップ以内で完了 |
| 3 | LINE未返信の見落とし | ゼロ（経過日数付きで管理） |
| 4 | メモの検索・呼び出し | 5秒以内 |

### 1.3 成功指標（KPI）

- 日次アクティブ利用率 > 80%（LINE対話ベース）
- メール返信承認率 > 70%（AI文案をそのまま or 微調整で送信）
- 未返信アイテム平均滞留日数 < 2日
- メモ検索ヒット率 > 90%

### 1.4 業務フロー（AI代替マップ）

| # | 現在の作業 | AI化後 | ユーザー操作 |
|---|-----------|--------|-------------|
| 1 | Gmailで新着確認 | AIが取得・分類・要約してLINE通知 | 要約を読むだけ |
| 2 | 返信文面を考えて手入力 | AI返信文案生成 | 確認→送信タップ or 微調整 |
| 3 | カレンダーアプリで確認 | LINEで聞くだけ | 回答を読むだけ |
| 4 | 空き時間を目視で探す | 空き時間候補を前後予定・場所付きで提示 | 候補選択→登録タップ |
| 5 | カレンダー通知を受動的に受ける | 朝サマリー+指定間隔リマインド | LINEで受取るだけ |
| 6 | LINE未返信を記憶頼み | 登録→経過日数追跡→リマインド | 登録→完了報告 |
| 7 | メモをバラバラに記録 | LINEに投げる→AI自動分類 | 送るだけ |
| 8 | 記事やURLを分散保存 | LINEに送る→AI要約+タグ付け | 検索で呼出し |

---

## 2. システム全体像

### 2.1 ユーザーロール

| ロール | 権限 | 説明 |
|--------|------|------|
| ゲスト（未登録） | 友だち追加・利用申請のみ | LINE友だち追加後、利用申請を行える |
| 一般ユーザー | AI秘書の全機能利用 | 管理者承認後に利用可能 |
| 管理者 | ユーザー承認・システム設定 | 利用申請の承認/却下、登録ユーザー管理 |

### 2.2 認証要件

- **認証方式**: LINE Login（OAuth 2.0）でWeb管理画面も統一認証
- **登録方式**: 承認制（友だち追加→利用申請→管理者承認）
- **トークン管理**: OAuthトークンは暗号化保存、アクセストークンはメモリ内のみ

### 2.3 機能一覧

#### メール管理
- Gmail新着取得 + AI自動分類（重要/参考/除外）
- メルマガ・広告・登録メール等は自動除外
  - 判定基準: List-Unsubscribeヘッダー、送信者ドメイン、件名パターン
- 重要メールのみ要約してLINE通知
- AI返信文案生成 → ユーザー承認 → 送信
- ユーザーがフィルタルール（送信者/ドメイン単位で重要/除外）を設定可能

#### スケジュール管理
- Googleカレンダー予定の確認・登録・変更・削除
- 空き時間候補検索
  - 前後の予定・場所を表示
  - 期間指定/所要時間指定対応
- 予定登録時の属性:
  - 種別: ビジネス / プライベート
  - 公開設定: 公開 / 非公開
  - 確定状態: 確定 / 仮予定
  - 場所
  - 色分け自動設定

**デフォルト色分けルール:**

| 種別 | 確定状態 | 色 |
|------|---------|-----|
| ビジネス | 確定 | 青 |
| ビジネス | 仮予定 | 薄青 |
| プライベート | 確定 | 緑 |
| プライベート | 仮予定 | 薄緑 |

- 色分けルールはユーザーがカスタマイズ可能

#### スケジュールリマインド
- 毎朝指定時間に今日の予定サマリーをLINE通知
- 予定開始前にユーザー指定間隔（30分前、15分前、5分前等）でリマインド通知
- 予定ごとの個別リマインド設定も可能

#### メモ管理
- LINEからテキスト・画像・URLを送信 → AI自動分類・カテゴリ付け・タグ付け
- カテゴリ: タスクリスト、買い物、アイデア、ZOOMアドレス、備忘録、記事、URL等
- 画像はOCR（Google Vision API）でテキスト抽出
- URL送信時はメタデータ取得 + AI要約
- 全文検索、カテゴリ別一覧、タグ検索
- 将来Notion連携を視野に置いた設計（メモデータの外部エクスポート対応）

#### LINE未返信管理
- 手動で「返信必要」と登録（相手名・内容メモ）
- 未返信経過日数の自動追跡
- 毎日のリマインド通知（閾値超えで警告）
- 「返信済み」で完了マーク

#### ショートカットワード入力
- 自然言語だけでなくキーワードの羅列でも情報取得可能
- AIがショートカットワードか自然言語かを自動判定

| 入力例 | 動作 |
|--------|------|
| 「予定」 | 今日の予定を表示 |
| 「メール」 | 未読重要メールを表示 |
| 「タスク 優先」 | 優先タスクを表示 |
| 「空き 来週」 | 来週の空き時間候補を表示 |
| 「未返信」 | 未返信リストを表示 |

#### LINEリッチメニュー
- 6分割: 予定確認 / メモ追加 / タスク管理 / リマインド / メール要約 / 設定

### 2.4 LINEとWebの役割分担

| チャネル | 役割 | 主な機能 |
|---------|------|---------|
| LINE（メイン） | 対話・登録・通知受信・簡易検索 | AI対話、メモ登録、通知受信、ショートカット |
| Web（補完） | 一覧性・編集・設定変更 | メモ一覧・編集、設定変更、ユーザー管理 |

### 2.5 処理依存関係

**並列実行可能（情報取得系）:**
- get_schedule, get_emails, find_available_slots, search_memo, list_unreplied

**直列実行（操作系 ← 取得系）:**
- send_email_reply ← get_emails
- create_event ← find_available_slots（推奨）
- update_event / delete_event ← get_schedule
- delete_memo ← search_memo
- complete_unreplied ← list_unreplied

### 2.6 定期実行フロー

| スケジュール | トリガー | 処理 |
|-------------|---------|------|
| 毎朝指定時間 | Cloud Scheduler | get_schedule → 予定サマリーPush通知 |
| 予定前指定間隔 | スケジューラ監視 | リマインドPush通知 |
| 毎日チェック | Cloud Scheduler | list_unreplied → 閾値超え → リマインドPush通知 |

---

## 3. ページ詳細仕様

### P-001: ログイン

| 項目 | 内容 |
|------|------|
| ルート | `/login` |
| 権限 | 全員 |
| 目的 | LINE連携認証、利用申請、承認待ち表示 |

**機能:**
- LINE Loginボタン（OAuth 2.0フロー開始）
- 利用申請フォーム（LINEアカウント連携後に表示）
- 承認待ちステータス表示
- 管理者承認後に自動リダイレクト（ワークスペースへ）

**処理フロー:**
1. ユーザーがLINE Loginボタンをクリック
2. LINE OAuth 2.0認証画面へリダイレクト
3. 認証成功後、コールバックURLでトークン取得
4. 未登録ユーザー → 利用申請画面を表示
5. 申請済み・承認待ち → ステータス表示
6. 承認済み → ワークスペースへリダイレクト

### P-002: ワークスペース

| 項目 | 内容 |
|------|------|
| ルート | `/` |
| 権限 | 一般ユーザー |
| 目的 | 今日の予定・未読メール要約・未返信リスト・最近のメモを一画面に集約 |

**機能:**
- 今日の予定一覧（Googleカレンダー連携）
- 未読重要メール要約リスト
- LINE未返信リスト（経過日数表示）
- 最近のメモ一覧
- 各項目からそのまま操作可能（返信文案生成、予定変更、メモ編集等）

**レイアウト:**
- 4セクションのダッシュボード形式
- レスポンシブ対応（モバイルは縦並び）

### P-003: メモ管理

| 項目 | 内容 |
|------|------|
| ルート | `/memos` |
| 権限 | 一般ユーザー |
| 目的 | カテゴリ別一覧、全文検索、画像/URLプレビュー、タグ編集、カテゴリ管理 |

**機能:**
- カテゴリ別タブ/フィルタ
- 全文検索バー
- メモカード表示（テキスト、画像プレビュー、URLプレビュー）
- タグ編集（インライン）
- カテゴリ管理（追加・名称変更・削除）
- メモの手動編集・削除
- エクスポート機能（JSON/CSV）

### P-004: 設定

| 項目 | 内容 |
|------|------|
| ルート | `/settings` |
| 権限 | 一般ユーザー |
| 目的 | 通知・連携・表示の設定管理 |

**機能:**
- 通知時間設定（朝サマリーの配信時間）
- リマインド間隔設定（30分前、15分前、5分前等の選択）
- Gmail連携（OAuth 2.0認証フロー）
- Googleカレンダー連携（OAuth 2.0認証フロー）
- カレンダー色分けルール設定
- メールフィルタ設定（送信者/ドメイン単位で重要/除外指定）

### A-001: ユーザー管理（管理者）

| 項目 | 内容 |
|------|------|
| ルート | `/admin/users` |
| 権限 | 管理者 |
| 目的 | 利用申請一覧、承認/却下、登録ユーザー一覧 |

**機能:**
- 利用申請一覧（未処理のみフィルタ）
- 承認/却下アクション（理由入力可）
- 登録ユーザー一覧（ステータス表示）
- ユーザー詳細（LINE表示名、申請日、承認日、最終利用日）
- ユーザー無効化/再有効化

---

## 4. データ設計概要

### 4.1 エンティティ一覧

#### User（ユーザー）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | ユーザーID |
| line_user_id | VARCHAR(64) | UNIQUE, NOT NULL | LINE ユーザーID |
| line_display_name | VARCHAR(128) | | LINE表示名 |
| line_picture_url | TEXT | | LINEプロフィール画像URL |
| role | ENUM | NOT NULL, DEFAULT 'guest' | guest / user / admin |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending / approved / rejected / disabled |
| applied_at | TIMESTAMP | | 利用申請日時 |
| approved_at | TIMESTAMP | | 承認日時 |
| approved_by | UUID | FK(User) | 承認者ID |
| rejection_reason | TEXT | | 却下理由 |
| last_active_at | TIMESTAMP | | 最終利用日時 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新日時 |

#### OAuthToken（OAuth トークン）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | トークンID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| provider | ENUM | NOT NULL | line / gmail / gcalendar |
| access_token_encrypted | BYTEA | NOT NULL | アクセストークン（AES-256暗号化） |
| refresh_token_encrypted | BYTEA | NOT NULL | リフレッシュトークン（AES-256暗号化） |
| expires_at | TIMESTAMP | NOT NULL | アクセストークン有効期限 |
| scopes | TEXT[] | | 認可スコープ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

#### Memo（メモ）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | メモID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| content | TEXT | NOT NULL | メモ本文 |
| content_type | ENUM | NOT NULL | text / image / url |
| category_id | UUID | FK(MemoCategory) | カテゴリID |
| tags | TEXT[] | DEFAULT '{}' | タグ配列 |
| image_url | TEXT | | 画像URL（GCS） |
| image_ocr_text | TEXT | | OCR抽出テキスト |
| url | TEXT | | 保存URL |
| url_title | TEXT | | URLメタタイトル |
| url_summary | TEXT | | AI生成の要約 |
| url_thumbnail | TEXT | | OGP画像URL |
| is_deleted | BOOLEAN | DEFAULT FALSE | 論理削除フラグ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

#### MemoCategory（メモカテゴリ）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | カテゴリID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| name | VARCHAR(64) | NOT NULL | カテゴリ名 |
| sort_order | INTEGER | DEFAULT 0 | 表示順 |
| is_default | BOOLEAN | DEFAULT FALSE | デフォルトカテゴリフラグ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**デフォルトカテゴリ:** タスクリスト、買い物、アイデア、ZOOMアドレス、備忘録、記事、URL

#### EmailFilter（メールフィルタ）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | フィルタID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| filter_type | ENUM | NOT NULL | sender / domain / subject_pattern |
| filter_value | VARCHAR(256) | NOT NULL | フィルタ値 |
| action | ENUM | NOT NULL | important / exclude |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**ユニーク制約:** (user_id, filter_type, filter_value)

#### UnrepliedItem（LINE未返信アイテム）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | アイテムID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| contact_name | VARCHAR(128) | NOT NULL | 相手名 |
| content_memo | TEXT | | 内容メモ |
| registered_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 登録日時 |
| completed_at | TIMESTAMP | | 完了日時 |
| is_completed | BOOLEAN | DEFAULT FALSE | 完了フラグ |
| days_elapsed | INTEGER | GENERATED | 経過日数（計算カラム） |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

#### EventColorRule（カレンダー色分けルール）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | ルールID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| event_type | ENUM | NOT NULL | business / private |
| confirmation_status | ENUM | NOT NULL | confirmed / tentative |
| color_id | VARCHAR(16) | NOT NULL | Googleカレンダー色ID |
| color_label | VARCHAR(32) | | 色ラベル（表示用） |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**ユニーク制約:** (user_id, event_type, confirmation_status)

#### NotificationSetting（通知設定）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 設定ID |
| user_id | UUID | FK(User), UNIQUE, NOT NULL | ユーザーID |
| morning_summary_time | TIME | DEFAULT '08:00' | 朝サマリー配信時間 |
| morning_summary_enabled | BOOLEAN | DEFAULT TRUE | 朝サマリー有効 |
| reminder_intervals | INTEGER[] | DEFAULT '{30,15,5}' | リマインド間隔（分） |
| unreplied_threshold_days | INTEGER | DEFAULT 3 | 未返信警告閾値（日数） |
| unreplied_reminder_enabled | BOOLEAN | DEFAULT TRUE | 未返信リマインド有効 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

#### EditHistory（変更履歴）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 履歴ID |
| user_id | UUID | FK(User), NOT NULL | ユーザーID |
| entity_type | VARCHAR(64) | NOT NULL | エンティティ種別 |
| entity_id | UUID | NOT NULL | 対象エンティティID |
| action | ENUM | NOT NULL | create / update / delete |
| before_data | JSONB | | 変更前データ |
| after_data | JSONB | | 変更後データ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

#### AuditLog（監査ログ）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | ログID |
| user_id | UUID | FK(User) | ユーザーID（未認証操作はNULL） |
| action | VARCHAR(128) | NOT NULL | 操作種別 |
| resource | VARCHAR(128) | | 対象リソース |
| resource_id | UUID | | 対象リソースID |
| ip_address | INET | | IPアドレス |
| user_agent | TEXT | | User-Agent |
| metadata | JSONB | | 追加メタデータ |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 作成日時 |

### 4.2 エンティティ関係図（テキスト）

```
User 1──* OAuthToken
User 1──* Memo
User 1──* MemoCategory
User 1──* EmailFilter
User 1──* UnrepliedItem
User 1──* EventColorRule
User 1──1 NotificationSetting
User 1──* EditHistory
User 1──* AuditLog
Memo *──1 MemoCategory
```

### 4.3 バリデーションルール

| エンティティ | フィールド | ルール |
|-------------|----------|--------|
| User | line_user_id | 必須、一意、最大64文字 |
| Memo | content | 必須、最大10,000文字 |
| Memo | tags | 各タグ最大32文字、最大20個 |
| MemoCategory | name | 必須、最大64文字、ユーザー内で一意 |
| EmailFilter | filter_value | 必須、最大256文字 |
| UnrepliedItem | contact_name | 必須、最大128文字 |
| EventColorRule | color_id | Googleカレンダー色ID（1-11） |
| NotificationSetting | morning_summary_time | 有効な時間値（00:00-23:59） |
| NotificationSetting | reminder_intervals | 各値1-1440の範囲 |
| NotificationSetting | unreplied_threshold_days | 1-30の範囲 |

---

## 5. セキュリティ要件

### 5.1 通信セキュリティ
- 全通信HTTPS（TLS 1.3）
- LINE Webhook署名検証（X-Line-Signature）

### 5.2 データ保護
- 保存データAES-256暗号化（OAuthトークン等）
- OAuthトークンは暗号化保存、アクセストークンはメモリ内のみ
- ユーザー間データ完全分離（クエリに必ずuser_idフィルタ）

### 5.3 認証・認可
- LINE Login（OAuth 2.0）による統一認証
- ブルートフォース対策不要（LINE Login利用のため）
- CSRF対策: トークン必須（Web管理画面）

### 5.4 入力値処理
- 入力値サニタイゼーション: 全エンドポイント
- SQLインジェクション対策: パラメータバインド（SQLAlchemy ORM）

### 5.5 AI関連
- AI API opt-out: ユーザーデータを学習に使用しない

### 5.6 運用
- 監査ログ: 全操作記録
- ヘルスチェック: `/api/health`
- グレースフルシャットダウン: SIGTERM対応、8秒タイムアウト

---

## 6. 技術スタック

```yaml
frontend:
  framework: React 18 + TypeScript 5 + MUI v6
  bundler: Vite 5
  routing: React Router v6
  state: Zustand
  api: React Query
  deploy: Vercel

backend:
  framework: Python 3.12+ + FastAPI
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

---

## 7. 外部サービス一覧

| API名 | 用途 | 認証方式 | 備考 |
|-------|------|---------|------|
| LINE Messaging API | Bot対話・通知・リッチメニュー | チャネルアクセストークン | Webhook受信 |
| LINE Login API | Web認証 | OAuth 2.0 | コールバックURL登録必須 |
| Gmail API | メール取得・返信 | OAuth 2.0 / Domain-wide Delegation | スコープ: gmail.readonly, gmail.send |
| Google Calendar API | 予定CRUD・FreeBusy | OAuth 2.0 / Domain-wide Delegation | スコープ: calendar.events |
| Anthropic Claude API | AI秘書（Tool Use自律ループ） | APIキー | Claude Sonnet 4.5 |
| Google Cloud Storage | 画像メモ保存 | サービスアカウント | バケット設定必要 |
| Google Cloud Vision API | 画像OCR | サービスアカウント | テキスト検出 |

---

## 8. AI設計

### 8.1 アーキテクチャ

- **オーケストレータ**: Claude Sonnet 4.5（Tool Use自律ループ）
- **max_turns**: 10
- **通信方式**:
  - LINE ↔ バックエンド: Webhook / Reply / Push
  - Web ↔ バックエンド: SSE（Server-Sent Events）
  - バックエンド ↔ Claude: Anthropic SDK

### 8.2 ストリーミング仕様（SSE）

Web管理画面向けのSSEイベントタイプ:

| イベントタイプ | 説明 | ペイロード例 |
|--------------|------|------------|
| text | テキスト応答の部分配信 | `{"content": "..."}` |
| tool_start | ツール実行開始 | `{"tool": "get_schedule", "input": {...}}` |
| tool_end | ツール実行完了 | `{"tool": "get_schedule", "result": {...}}` |
| approval_request | ユーザー承認要求 | `{"action": "send_email", "details": {...}}` |
| error | エラー発生 | `{"message": "...", "code": "..."}` |
| done | 応答完了 | `{}` |

### 8.3 ツール定義（15ツール）

#### スケジュール管理系

```json
{
  "name": "get_schedule",
  "description": "指定日付範囲のGoogleカレンダー予定を取得する",
  "input_schema": {
    "type": "object",
    "properties": {
      "start_date": { "type": "string", "format": "date", "description": "開始日（YYYY-MM-DD）" },
      "end_date": { "type": "string", "format": "date", "description": "終了日（YYYY-MM-DD）。省略時はstart_dateと同日" }
    },
    "required": ["start_date"]
  }
}
```

```json
{
  "name": "find_available_slots",
  "description": "指定期間内の空き時間候補を検索する。前後の予定と場所も含めて返す",
  "input_schema": {
    "type": "object",
    "properties": {
      "start_date": { "type": "string", "format": "date", "description": "検索開始日" },
      "end_date": { "type": "string", "format": "date", "description": "検索終了日" },
      "duration_minutes": { "type": "integer", "description": "所要時間（分）", "default": 60 },
      "time_range_start": { "type": "string", "format": "time", "description": "検索時間帯の開始（HH:MM）", "default": "09:00" },
      "time_range_end": { "type": "string", "format": "time", "description": "検索時間帯の終了（HH:MM）", "default": "18:00" }
    },
    "required": ["start_date", "end_date"]
  }
}
```

```json
{
  "name": "create_event",
  "description": "Googleカレンダーに新しい予定を作成する",
  "input_schema": {
    "type": "object",
    "properties": {
      "title": { "type": "string", "description": "予定タイトル" },
      "start_datetime": { "type": "string", "format": "date-time", "description": "開始日時" },
      "end_datetime": { "type": "string", "format": "date-time", "description": "終了日時" },
      "location": { "type": "string", "description": "場所" },
      "event_type": { "type": "string", "enum": ["business", "private"], "description": "種別" },
      "visibility": { "type": "string", "enum": ["public", "private"], "description": "公開設定" },
      "status": { "type": "string", "enum": ["confirmed", "tentative"], "description": "確定状態" },
      "description": { "type": "string", "description": "説明" }
    },
    "required": ["title", "start_datetime", "end_datetime"]
  }
}
```

```json
{
  "name": "update_event",
  "description": "既存のGoogleカレンダー予定を更新する",
  "input_schema": {
    "type": "object",
    "properties": {
      "event_id": { "type": "string", "description": "予定ID" },
      "title": { "type": "string" },
      "start_datetime": { "type": "string", "format": "date-time" },
      "end_datetime": { "type": "string", "format": "date-time" },
      "location": { "type": "string" },
      "event_type": { "type": "string", "enum": ["business", "private"] },
      "visibility": { "type": "string", "enum": ["public", "private"] },
      "status": { "type": "string", "enum": ["confirmed", "tentative"] },
      "description": { "type": "string" }
    },
    "required": ["event_id"]
  }
}
```

```json
{
  "name": "delete_event",
  "description": "Googleカレンダーの予定を削除する",
  "input_schema": {
    "type": "object",
    "properties": {
      "event_id": { "type": "string", "description": "予定ID" }
    },
    "required": ["event_id"]
  }
}
```

#### メール管理系

```json
{
  "name": "get_emails",
  "description": "Gmail受信トレイから未読メールを取得し、AI分類（重要/参考/除外）済みで返す",
  "input_schema": {
    "type": "object",
    "properties": {
      "max_results": { "type": "integer", "description": "最大取得件数", "default": 20 },
      "category": { "type": "string", "enum": ["important", "reference", "excluded", "all"], "default": "important" },
      "since_hours": { "type": "integer", "description": "何時間前からの取得か", "default": 24 }
    }
  }
}
```

```json
{
  "name": "send_email_reply",
  "description": "指定メールに対してAI生成の返信文案で返信する。ユーザー承認後に実行",
  "input_schema": {
    "type": "object",
    "properties": {
      "email_id": { "type": "string", "description": "返信対象メールID" },
      "reply_body": { "type": "string", "description": "返信本文" },
      "reply_subject": { "type": "string", "description": "返信件名（省略時はRe:元件名）" }
    },
    "required": ["email_id", "reply_body"]
  }
}
```

```json
{
  "name": "set_email_filter",
  "description": "メールフィルタルールを作成・更新する",
  "input_schema": {
    "type": "object",
    "properties": {
      "filter_type": { "type": "string", "enum": ["sender", "domain", "subject_pattern"], "description": "フィルタ種別" },
      "filter_value": { "type": "string", "description": "フィルタ値" },
      "action": { "type": "string", "enum": ["important", "exclude"], "description": "適用アクション" }
    },
    "required": ["filter_type", "filter_value", "action"]
  }
}
```

#### メモ管理系

```json
{
  "name": "save_memo",
  "description": "メモを保存する。AI自動分類でカテゴリ・タグを付与",
  "input_schema": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "メモ本文" },
      "content_type": { "type": "string", "enum": ["text", "image", "url"], "default": "text" },
      "image_data": { "type": "string", "description": "Base64エンコードされた画像データ" },
      "url": { "type": "string", "description": "保存するURL" },
      "category_name": { "type": "string", "description": "カテゴリ名（AI自動判定を上書き）" },
      "tags": { "type": "array", "items": { "type": "string" }, "description": "タグ（AI自動判定を上書き）" }
    },
    "required": ["content"]
  }
}
```

```json
{
  "name": "search_memo",
  "description": "メモを検索する。全文検索、カテゴリ、タグで絞り込み可能",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "検索キーワード" },
      "category_name": { "type": "string", "description": "カテゴリ名で絞り込み" },
      "tags": { "type": "array", "items": { "type": "string" }, "description": "タグで絞り込み" },
      "limit": { "type": "integer", "default": 10 }
    }
  }
}
```

```json
{
  "name": "delete_memo",
  "description": "指定メモを論理削除する",
  "input_schema": {
    "type": "object",
    "properties": {
      "memo_id": { "type": "string", "description": "メモID" }
    },
    "required": ["memo_id"]
  }
}
```

#### LINE未返信管理系

```json
{
  "name": "register_unreplied",
  "description": "LINE未返信アイテムを登録する",
  "input_schema": {
    "type": "object",
    "properties": {
      "contact_name": { "type": "string", "description": "相手名" },
      "content_memo": { "type": "string", "description": "内容メモ" }
    },
    "required": ["contact_name"]
  }
}
```

```json
{
  "name": "list_unreplied",
  "description": "未返信アイテム一覧を取得する。経過日数付き",
  "input_schema": {
    "type": "object",
    "properties": {
      "include_completed": { "type": "boolean", "default": false, "description": "完了済みも含める" }
    }
  }
}
```

```json
{
  "name": "complete_unreplied",
  "description": "未返信アイテムを返信済み（完了）にする",
  "input_schema": {
    "type": "object",
    "properties": {
      "item_id": { "type": "string", "description": "未返信アイテムID" }
    },
    "required": ["item_id"]
  }
}
```

#### 管理系

```json
{
  "name": "approve_user",
  "description": "ユーザーの利用申請を承認する（管理者専用）",
  "input_schema": {
    "type": "object",
    "properties": {
      "target_user_id": { "type": "string", "description": "対象ユーザーID" },
      "action": { "type": "string", "enum": ["approve", "reject"], "description": "承認/却下" },
      "reason": { "type": "string", "description": "却下理由（却下時のみ）" }
    },
    "required": ["target_user_id", "action"]
  }
}
```

### 8.4 自律ループ仕様

1. ユーザーメッセージ受信（LINE Webhook or Web SSE）
2. Claude にメッセージ + ツール定義 + システムプロンプトを送信
3. Claude がツール呼び出しを返す場合:
   - ツール実行（並列可能なものは並列実行）
   - 結果を Claude に返す
   - max_turns に達するか、Claude がテキスト応答を返すまで繰り返し
4. 承認が必要な操作（send_email_reply, delete_event等）はユーザー確認後に実行
5. 最終テキスト応答をユーザーに返す

### 8.5 非破壊編集の方針

- メモはカテゴリ・タグ単位でJSON管理
- 修正対象のみ更新、他は変更しない
- 全変更に対してEditHistoryレコード作成
