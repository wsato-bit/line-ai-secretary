"""LINE Flex Messageテンプレート集"""

from datetime import datetime


def schedule_summary_template(events: list[dict]) -> dict:
    """予定サマリーFlex Message。

    Args:
        events: [{"title": str, "start": str, "end": str, "location": str|None}, ...]
    """
    if not events:
        return _empty_bubble("予定サマリー", "本日の予定はありません。")

    body_contents = [
        {
            "type": "text",
            "text": "本日の予定",
            "weight": "bold",
            "size": "lg",
            "color": "#1a1a1a",
        },
        {"type": "separator", "margin": "md"},
    ]

    for ev in events[:10]:
        time_str = ev.get("start", "")
        if ev.get("end"):
            time_str += f" - {ev['end']}"
        item = {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": ev.get("title", "無題"),
                    "weight": "bold",
                    "size": "sm",
                    "color": "#1a1a1a",
                },
                {
                    "type": "text",
                    "text": time_str,
                    "size": "xs",
                    "color": "#888888",
                },
            ],
        }
        if ev.get("location"):
            item["contents"].append(
                {
                    "type": "text",
                    "text": f"📍 {ev['location']}",
                    "size": "xs",
                    "color": "#666666",
                }
            )
        body_contents.append(item)

    return {
        "type": "bubble",
        "header": _header("📅 予定サマリー"),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "spacing": "sm",
        },
    }


def email_summary_template(emails: list[dict]) -> dict:
    """メール要約Flex Message。

    Args:
        emails: [{"from": str, "subject": str, "summary": str, "priority": str}, ...]
    """
    if not emails:
        return _empty_bubble("メール要約", "未読の重要メールはありません。")

    body_contents = [
        {
            "type": "text",
            "text": f"未読メール {len(emails)}件",
            "weight": "bold",
            "size": "lg",
            "color": "#1a1a1a",
        },
        {"type": "separator", "margin": "md"},
    ]

    for mail in emails[:5]:
        priority_color = "#ff4444" if mail.get("priority") == "high" else "#888888"
        body_contents.append(
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": mail.get("subject", "件名なし"),
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True,
                        "color": priority_color,
                    },
                    {
                        "type": "text",
                        "text": f"From: {mail.get('from', '不明')}",
                        "size": "xs",
                        "color": "#888888",
                    },
                    {
                        "type": "text",
                        "text": mail.get("summary", "")[:80],
                        "size": "xs",
                        "color": "#555555",
                        "wrap": True,
                    },
                ],
            }
        )

    return {
        "type": "bubble",
        "header": _header("📧 メール要約"),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "spacing": "sm",
        },
    }


def unreplied_list_template(items: list[dict]) -> dict:
    """未返信リストFlex Message。

    Args:
        items: [{"type": str, "from": str, "subject": str, "received_at": str}, ...]
    """
    if not items:
        return _empty_bubble("未返信リスト", "未返信の項目はありません。")

    body_contents = [
        {
            "type": "text",
            "text": f"未返信 {len(items)}件",
            "weight": "bold",
            "size": "lg",
            "color": "#ff4444",
        },
        {"type": "separator", "margin": "md"},
    ]

    for item in items[:10]:
        icon = "📧" if item.get("type") == "email" else "💬"
        body_contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": icon,
                        "size": "sm",
                        "flex": 0,
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": 1,
                        "margin": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": item.get("subject", "件名なし"),
                                "weight": "bold",
                                "size": "xs",
                                "wrap": True,
                            },
                            {
                                "type": "text",
                                "text": f"{item.get('from', '不明')} / {item.get('received_at', '')}",
                                "size": "xxs",
                                "color": "#888888",
                            },
                        ],
                    },
                ],
            }
        )

    return {
        "type": "bubble",
        "header": _header("⚠️ 未返信リスト"),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "spacing": "sm",
        },
    }


def memo_saved_template(memo: dict) -> dict:
    """メモ保存確認Flex Message。

    Args:
        memo: {"id": str, "content": str, "tags": list[str], "saved_at": str}
    """
    tags_text = " ".join(f"#{t}" for t in memo.get("tags", [])) or "タグなし"
    saved_at = memo.get("saved_at", datetime.now().strftime("%Y-%m-%d %H:%M"))

    return {
        "type": "bubble",
        "header": _header("📝 メモ保存完了"),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": memo.get("content", "")[:200],
                    "wrap": True,
                    "size": "sm",
                    "color": "#333333",
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "text",
                    "text": tags_text,
                    "size": "xs",
                    "color": "#06C755",
                    "margin": "md",
                },
                {
                    "type": "text",
                    "text": f"保存日時: {saved_at}",
                    "size": "xxs",
                    "color": "#888888",
                    "margin": "sm",
                },
            ],
            "spacing": "sm",
        },
    }


def approval_request_template(action: str, details: dict) -> dict:
    """承認要求Flex Message（管理者向け）。

    Args:
        action: 承認対象アクション名
        details: {"user_id": str, "display_name": str, "description": str}
    """
    user_id = details.get("user_id", "")
    display_name = details.get("display_name", "不明")
    description = details.get("description", "")

    return {
        "type": "bubble",
        "header": _header("🔔 承認リクエスト"),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"アクション: {action}",
                    "weight": "bold",
                    "size": "sm",
                },
                {
                    "type": "text",
                    "text": f"ユーザー: {display_name}",
                    "size": "sm",
                    "color": "#555555",
                    "margin": "sm",
                },
                {
                    "type": "text",
                    "text": description[:150] if description else "詳細なし",
                    "size": "xs",
                    "color": "#888888",
                    "wrap": True,
                    "margin": "sm",
                },
            ],
            "spacing": "sm",
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#06C755",
                    "action": {
                        "type": "postback",
                        "label": "承認",
                        "data": f"action=approve&user_id={user_id}",
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "postback",
                        "label": "拒否",
                        "data": f"action=reject&user_id={user_id}",
                    },
                },
            ],
        },
    }


def _header(title: str) -> dict:
    """共通ヘッダー。"""
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": "#06C755",
        "paddingAll": "lg",
        "contents": [
            {
                "type": "text",
                "text": title,
                "color": "#ffffff",
                "weight": "bold",
                "size": "md",
            }
        ],
    }


def _empty_bubble(title: str, message: str) -> dict:
    """データなし時の空バブル。"""
    return {
        "type": "bubble",
        "header": _header(title),
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": message,
                    "size": "sm",
                    "color": "#888888",
                    "align": "center",
                }
            ],
        },
    }
