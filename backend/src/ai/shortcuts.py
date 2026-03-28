"""ショートカットワード検出 - メッセージ前処理でエージェントにヒントを付加"""

import re
from dataclasses import dataclass


@dataclass
class ShortcutHint:
    """ショートカット検出結果。"""

    original_message: str
    hint_prefix: str
    detected_keyword: str


# ショートカット定義: (パターン, ヒントプレフィックス)
_SHORTCUT_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"(予定|スケジュール|カレンダー)", re.IGNORECASE),
        "[ユーザーはスケジュールについて話しています。get_scheduleツールの使用を検討してください。]\n\n",
        "schedule",
    ),
    (
        re.compile(r"(空き時間|空いてる|いつ空|アポ|打ち合わせ調整)", re.IGNORECASE),
        "[ユーザーは空き時間を探しています。find_available_slotsツールの使用を検討してください。]\n\n",
        "available_slots",
    ),
    (
        re.compile(r"(メール|受信|inbox)", re.IGNORECASE),
        "[ユーザーはメールについて話しています。get_emailsツールの使用を検討してください。]\n\n",
        "email",
    ),
    (
        re.compile(r"(メモして|メモ保存|覚えて|記録して)", re.IGNORECASE),
        "[ユーザーはメモを保存したいようです。save_memoツールの使用を検討してください。]\n\n",
        "save_memo",
    ),
    (
        re.compile(r"(メモ検索|メモ一覧|メモを探|思い出)", re.IGNORECASE),
        "[ユーザーはメモを検索したいようです。search_memoツールの使用を検討してください。]\n\n",
        "search_memo",
    ),
    (
        re.compile(r"(未返信|返信してない|返事してない|まだ返し)", re.IGNORECASE),
        "[ユーザーは未返信リストについて話しています。list_unrepliedツールの使用を検討してください。]\n\n",
        "unreplied",
    ),
    (
        re.compile(r"(リマインド|リマインダー|忘れないで|通知して)", re.IGNORECASE),
        "[ユーザーはリマインダー・通知について話しています。スケジュールやメモ機能と組み合わせて対応してください。]\n\n",
        "reminder",
    ),
    (
        re.compile(r"(承認|ユーザー承認|利用許可)", re.IGNORECASE),
        "[ユーザーはユーザー承認について話しています。approve_userツールの使用を検討してください（管理者権限が必要）。]\n\n",
        "approve",
    ),
]


def detect_shortcut(message: str) -> ShortcutHint | None:
    """メッセージからショートカットワードを検出し、ヒント付きメッセージを返す。

    Args:
        message: ユーザーの入力メッセージ

    Returns:
        ShortcutHint（検出時）またはNone
    """
    for pattern, hint, keyword in _SHORTCUT_PATTERNS:
        if pattern.search(message):
            return ShortcutHint(
                original_message=message,
                hint_prefix=hint,
                detected_keyword=keyword,
            )
    return None


def apply_shortcut(message: str) -> str:
    """メッセージにショートカットヒントを適用して返す。

    検出されなかった場合は元のメッセージをそのまま返す。
    """
    hint = detect_shortcut(message)
    if hint:
        return hint.hint_prefix + hint.original_message
    return message
