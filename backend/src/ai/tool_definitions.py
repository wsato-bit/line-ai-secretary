"""Anthropic Tool Use API用のツール定義（JSON Schema）"""

TOOL_DEFINITIONS: list[dict] = [
    # ─── Schedule ──────────────────────────────────────────────
    {
        "name": "get_schedule",
        "description": "指定日のスケジュール（予定一覧）を取得します。日付を省略した場合は今日の予定を返します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "取得対象の日付（YYYY-MM-DD形式）。省略時は今日。",
                },
                "days": {
                    "type": "integer",
                    "description": "取得する日数（1〜7）。デフォルト1。",
                    "default": 1,
                },
            },
            "required": [],
        },
    },
    {
        "name": "find_available_slots",
        "description": "指定日の空き時間帯を検索します。会議の調整などに使用します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "検索対象の日付（YYYY-MM-DD形式）。",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "必要な時間（分単位）。デフォルト60。",
                    "default": 60,
                },
                "start_hour": {
                    "type": "integer",
                    "description": "検索開始時刻（時）。デフォルト9。",
                    "default": 9,
                },
                "end_hour": {
                    "type": "integer",
                    "description": "検索終了時刻（時）。デフォルト18。",
                    "default": 18,
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "create_event",
        "description": "Googleカレンダーに新しい予定を作成します。実行前にユーザーの承認が必要です。",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "予定のタイトル。",
                },
                "date": {
                    "type": "string",
                    "description": "日付（YYYY-MM-DD形式）。",
                },
                "start_time": {
                    "type": "string",
                    "description": "開始時刻（HH:MM形式）。",
                },
                "end_time": {
                    "type": "string",
                    "description": "終了時刻（HH:MM形式）。",
                },
                "description": {
                    "type": "string",
                    "description": "予定の説明（任意）。",
                },
                "location": {
                    "type": "string",
                    "description": "場所（任意）。",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["business", "private"],
                    "description": "予定の種類。デフォルトはbusiness。",
                    "default": "business",
                },
            },
            "required": ["title", "date", "start_time", "end_time"],
        },
    },
    {
        "name": "update_event",
        "description": "既存の予定を更新します。変更したいフィールドのみ指定してください。",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "更新対象の予定ID。",
                },
                "title": {
                    "type": "string",
                    "description": "新しいタイトル。",
                },
                "date": {
                    "type": "string",
                    "description": "新しい日付（YYYY-MM-DD形式）。",
                },
                "start_time": {
                    "type": "string",
                    "description": "新しい開始時刻（HH:MM形式）。",
                },
                "end_time": {
                    "type": "string",
                    "description": "新しい終了時刻（HH:MM形式）。",
                },
                "description": {
                    "type": "string",
                    "description": "新しい説明。",
                },
                "location": {
                    "type": "string",
                    "description": "新しい場所。",
                },
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "delete_event",
        "description": "指定した予定を削除します。実行前にユーザーの承認が必要です。",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "削除対象の予定ID。",
                },
                "reason": {
                    "type": "string",
                    "description": "削除理由（任意）。",
                },
            },
            "required": ["event_id"],
        },
    },
    # ─── Email ─────────────────────────────────────────────────
    {
        "name": "get_emails",
        "description": "未読メールや重要メールの一覧を取得します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["unread", "important", "all"],
                    "description": "フィルタ種別。デフォルトはunread。",
                    "default": "unread",
                },
                "limit": {
                    "type": "integer",
                    "description": "取得件数上限。デフォルト10。",
                    "default": 10,
                },
                "sender": {
                    "type": "string",
                    "description": "送信者でフィルタ（任意）。",
                },
            },
            "required": [],
        },
    },
    {
        "name": "send_email_reply",
        "description": "指定したメールに返信を送信します。実行前にユーザーの承認が必要です。",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "返信対象のメールID。",
                },
                "body": {
                    "type": "string",
                    "description": "返信本文。",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CCに追加するメールアドレス（任意）。",
                },
            },
            "required": ["email_id", "body"],
        },
    },
    {
        "name": "set_email_filter",
        "description": "メールフィルタールールを設定します。特定の送信者やドメインに対する処理を定義します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_type": {
                    "type": "string",
                    "enum": ["sender", "domain", "subject_pattern"],
                    "description": "フィルタの種類。",
                },
                "filter_value": {
                    "type": "string",
                    "description": "フィルタ条件の値（メールアドレス、ドメイン、件名パターン）。",
                },
                "action": {
                    "type": "string",
                    "enum": ["important", "exclude"],
                    "description": "一致時のアクション。importantは重要マーク、excludeは除外。",
                },
            },
            "required": ["filter_type", "filter_value", "action"],
        },
    },
    # ─── Memo ──────────────────────────────────────────────────
    {
        "name": "save_memo",
        "description": "メモを保存します。テキスト、URL、画像いずれかの形式で保存できます。",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "メモの本文。",
                },
                "content_type": {
                    "type": "string",
                    "enum": ["text", "url", "image"],
                    "description": "メモの種類。デフォルトはtext。",
                    "default": "text",
                },
                "category": {
                    "type": "string",
                    "description": "カテゴリ名（任意）。",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "タグ（任意）。",
                },
                "url": {
                    "type": "string",
                    "description": "URLメモの場合のURL。",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "search_memo",
        "description": "キーワードやカテゴリでメモを検索します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "検索キーワード。",
                },
                "category": {
                    "type": "string",
                    "description": "カテゴリでフィルタ（任意）。",
                },
                "tag": {
                    "type": "string",
                    "description": "タグでフィルタ（任意）。",
                },
                "limit": {
                    "type": "integer",
                    "description": "取得件数上限。デフォルト10。",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "delete_memo",
        "description": "指定したメモを削除（論理削除）します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "memo_id": {
                    "type": "string",
                    "description": "削除対象のメモID。",
                },
            },
            "required": ["memo_id"],
        },
    },
    # ─── Unreplied ─────────────────────────────────────────────
    {
        "name": "register_unreplied",
        "description": "返信が必要な連絡先を未返信リストに登録します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_name": {
                    "type": "string",
                    "description": "連絡先の名前。",
                },
                "content_memo": {
                    "type": "string",
                    "description": "用件のメモ（任意）。",
                },
            },
            "required": ["contact_name"],
        },
    },
    {
        "name": "list_unreplied",
        "description": "未返信リストを表示します。未完了のもののみ表示します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_completed": {
                    "type": "boolean",
                    "description": "完了済みも含めるかどうか。デフォルトfalse。",
                    "default": False,
                },
            },
            "required": [],
        },
    },
    {
        "name": "complete_unreplied",
        "description": "未返信リストの項目を返信済みに変更します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "unreplied_id": {
                    "type": "string",
                    "description": "完了にする未返信項目のID。",
                },
            },
            "required": ["unreplied_id"],
        },
    },
    # ─── Admin ─────────────────────────────────────────────────
    {
        "name": "approve_user",
        "description": "管理者がユーザーの利用を承認します。管理者権限が必要です。実行前にユーザーの承認が必要です。",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_user_id": {
                    "type": "string",
                    "description": "承認対象のユーザーID（LINE user ID）。",
                },
                "approve": {
                    "type": "boolean",
                    "description": "trueで承認、falseで拒否。",
                },
                "reason": {
                    "type": "string",
                    "description": "拒否の場合の理由（任意）。",
                },
            },
            "required": ["target_user_id", "approve"],
        },
    },
]

# 承認が必要なツール名のセット
APPROVAL_REQUIRED_TOOLS: set[str] = {
    "create_event",
    "delete_event",
    "send_email_reply",
    "approve_user",
}
