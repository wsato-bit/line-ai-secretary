"""ツールディスパッチャ - ツール名に応じて適切なサービス関数にルーティング"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.ai.tool_definitions import APPROVAL_REQUIRED_TOOLS
from src.models.models import (
    ContentType,
    EmailFilter,
    EmailFilterAction,
    EmailFilterType,
    Memo,
    MemoCategory,
    UnrepliedItem,
    User,
    UserStatus,
)

logger = logging.getLogger(__name__)


class ApprovalRequest:
    """承認リクエストを表すデータクラス。"""

    def __init__(self, tool_name: str, tool_input: dict, description: str):
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.description = description

    def to_dict(self) -> dict:
        return {
            "type": "approval_request",
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "description": self.description,
        }


async def dispatch(
    tool_name: str,
    tool_input: dict,
    user_id: str,
    db: Session,
    force_execute: bool = False,
) -> dict | ApprovalRequest:
    """ツールを実行し結果を返す。承認必要ツールはApprovalRequestを返す。

    Args:
        tool_name: 実行するツール名
        tool_input: ツールへの入力パラメータ
        user_id: 実行ユーザーのLINE user ID
        db: データベースセッション
        force_execute: True の場合、承認チェックをスキップして実行

    Returns:
        ツール実行結果のdict、または ApprovalRequest
    """
    # 承認が必要なツールの場合
    if tool_name in APPROVAL_REQUIRED_TOOLS and not force_execute:
        description = _build_approval_description(tool_name, tool_input)
        return ApprovalRequest(tool_name, tool_input, description)

    # ツールルーティング
    handler = _TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"不明なツール: {tool_name}"}

    try:
        result = await handler(tool_input, user_id, db)
        return result
    except Exception as e:
        logger.exception("Tool execution failed: %s", tool_name)
        return {"error": f"ツール実行エラー: {str(e)}"}


# ─── Handler implementations ─────────────────────────────────


async def _handle_get_schedule(params: dict, user_id: str, db: Session) -> dict:
    """スケジュール取得。Google Calendar API連携（現在はスタブ）。"""
    date = params.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    days = params.get("days", 1)
    # TODO: Google Calendar API連携
    return {
        "status": "ok",
        "date": date,
        "days": days,
        "events": [],
        "message": f"{date}から{days}日分の予定はありません。",
    }


async def _handle_find_available_slots(params: dict, user_id: str, db: Session) -> dict:
    """空き時間検索。"""
    date = params["date"]
    duration = params.get("duration_minutes", 60)
    start_h = params.get("start_hour", 9)
    end_h = params.get("end_hour", 18)
    # TODO: Google Calendar API連携
    return {
        "status": "ok",
        "date": date,
        "available_slots": [
            {"start": f"{start_h:02d}:00", "end": f"{end_h:02d}:00"}
        ],
        "message": f"{date}は{start_h}時〜{end_h}時が空いています。",
    }


async def _handle_create_event(params: dict, user_id: str, db: Session) -> dict:
    """予定作成。"""
    # TODO: Google Calendar API連携
    return {
        "status": "ok",
        "message": (
            f"予定を作成しました: {params['title']} "
            f"({params['date']} {params['start_time']}〜{params['end_time']})"
        ),
    }


async def _handle_update_event(params: dict, user_id: str, db: Session) -> dict:
    """予定更新。"""
    event_id = params["event_id"]
    # TODO: Google Calendar API連携
    updates = {k: v for k, v in params.items() if k != "event_id"}
    return {
        "status": "ok",
        "event_id": event_id,
        "updated_fields": list(updates.keys()),
        "message": f"予定（ID: {event_id}）を更新しました。",
    }


async def _handle_delete_event(params: dict, user_id: str, db: Session) -> dict:
    """予定削除。"""
    event_id = params["event_id"]
    # TODO: Google Calendar API連携
    return {
        "status": "ok",
        "event_id": event_id,
        "message": f"予定（ID: {event_id}）を削除しました。",
    }


async def _handle_get_emails(params: dict, user_id: str, db: Session) -> dict:
    """メール一覧取得。"""
    filter_type = params.get("filter", "unread")
    limit = params.get("limit", 10)
    # TODO: Gmail API連携
    return {
        "status": "ok",
        "filter": filter_type,
        "emails": [],
        "message": f"{filter_type}メールはありません。",
    }


async def _handle_send_email_reply(params: dict, user_id: str, db: Session) -> dict:
    """メール返信送信。"""
    email_id = params["email_id"]
    # TODO: Gmail API連携
    return {
        "status": "ok",
        "email_id": email_id,
        "message": "メールを返信しました。",
    }


async def _handle_set_email_filter(params: dict, user_id: str, db: Session) -> dict:
    """メールフィルター設定。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    filter_type = EmailFilterType(params["filter_type"])
    action = EmailFilterAction(params["action"])
    filter_value = params["filter_value"]

    existing = (
        db.query(EmailFilter)
        .filter(
            EmailFilter.user_id == user.id,
            EmailFilter.filter_type == filter_type,
            EmailFilter.filter_value == filter_value,
        )
        .first()
    )
    if existing:
        existing.action = action
    else:
        new_filter = EmailFilter(
            user_id=user.id,
            filter_type=filter_type,
            filter_value=filter_value,
            action=action,
        )
        db.add(new_filter)

    db.commit()
    return {
        "status": "ok",
        "message": f"フィルターを設定しました: {filter_type.value}={filter_value} → {action.value}",
    }


async def _handle_save_memo(params: dict, user_id: str, db: Session) -> dict:
    """メモ保存。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    content_type = ContentType(params.get("content_type", "text"))
    category_id = None

    # カテゴリ指定がある場合
    cat_name = params.get("category")
    if cat_name:
        cat = (
            db.query(MemoCategory)
            .filter(MemoCategory.user_id == user.id, MemoCategory.name == cat_name)
            .first()
        )
        if not cat:
            cat = MemoCategory(user_id=user.id, name=cat_name)
            db.add(cat)
            db.flush()
        category_id = cat.id

    memo = Memo(
        user_id=user.id,
        content=params["content"],
        content_type=content_type,
        category_id=category_id,
        tags=params.get("tags"),
        url=params.get("url"),
    )
    db.add(memo)
    db.commit()

    return {
        "status": "ok",
        "memo_id": str(memo.id),
        "message": "メモを保存しました。",
    }


async def _handle_search_memo(params: dict, user_id: str, db: Session) -> dict:
    """メモ検索。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    query = db.query(Memo).filter(Memo.user_id == user.id, Memo.is_deleted.is_(False))

    keyword = params.get("keyword")
    if keyword:
        query = query.filter(Memo.content.ilike(f"%{keyword}%"))

    cat_name = params.get("category")
    if cat_name:
        cat = (
            db.query(MemoCategory)
            .filter(MemoCategory.user_id == user.id, MemoCategory.name == cat_name)
            .first()
        )
        if cat:
            query = query.filter(Memo.category_id == cat.id)

    tag = params.get("tag")
    if tag:
        query = query.filter(Memo.tags.any(tag))

    limit = params.get("limit", 10)
    memos = query.order_by(Memo.created_at.desc()).limit(limit).all()

    results = []
    for m in memos:
        results.append({
            "memo_id": str(m.id),
            "content": m.content[:100],
            "content_type": m.content_type.value,
            "tags": m.tags or [],
            "created_at": m.created_at.isoformat(),
        })

    return {
        "status": "ok",
        "count": len(results),
        "memos": results,
        "message": f"{len(results)}件のメモが見つかりました。" if results else "メモは見つかりませんでした。",
    }


async def _handle_delete_memo(params: dict, user_id: str, db: Session) -> dict:
    """メモ削除（論理削除）。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    memo_id = params["memo_id"]
    try:
        memo_uuid = uuid.UUID(memo_id)
    except ValueError:
        return {"error": "無効なメモIDです。"}

    memo = (
        db.query(Memo)
        .filter(Memo.id == memo_uuid, Memo.user_id == user.id)
        .first()
    )
    if not memo:
        return {"error": "メモが見つかりません。"}

    memo.is_deleted = True
    db.commit()
    return {"status": "ok", "message": "メモを削除しました。"}


async def _handle_register_unreplied(params: dict, user_id: str, db: Session) -> dict:
    """未返信登録。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    item = UnrepliedItem(
        user_id=user.id,
        contact_name=params["contact_name"],
        content_memo=params.get("content_memo"),
    )
    db.add(item)
    db.commit()

    return {
        "status": "ok",
        "unreplied_id": str(item.id),
        "message": f"{params['contact_name']}さんへの未返信を登録しました。",
    }


async def _handle_list_unreplied(params: dict, user_id: str, db: Session) -> dict:
    """未返信リスト取得。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    query = db.query(UnrepliedItem).filter(UnrepliedItem.user_id == user.id)

    if not params.get("include_completed", False):
        query = query.filter(UnrepliedItem.is_completed.is_(False))

    items = query.order_by(UnrepliedItem.registered_at.desc()).all()

    results = []
    for item in items:
        results.append({
            "unreplied_id": str(item.id),
            "contact_name": item.contact_name,
            "content_memo": item.content_memo,
            "registered_at": item.registered_at.isoformat(),
            "is_completed": item.is_completed,
        })

    return {
        "status": "ok",
        "count": len(results),
        "items": results,
        "message": f"未返信が{len(results)}件あります。" if results else "未返信はありません。",
    }


async def _handle_complete_unreplied(params: dict, user_id: str, db: Session) -> dict:
    """未返信完了。"""
    user = db.query(User).filter(User.line_user_id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません。"}

    unreplied_id = params["unreplied_id"]
    try:
        item_uuid = uuid.UUID(unreplied_id)
    except ValueError:
        return {"error": "無効なIDです。"}

    item = (
        db.query(UnrepliedItem)
        .filter(UnrepliedItem.id == item_uuid, UnrepliedItem.user_id == user.id)
        .first()
    )
    if not item:
        return {"error": "未返信項目が見つかりません。"}

    item.is_completed = True
    item.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "ok",
        "message": f"{item.contact_name}さんへの返信を完了にしました。",
    }


async def _handle_approve_user(params: dict, user_id: str, db: Session) -> dict:
    """ユーザー承認（管理者専用）。"""
    admin = db.query(User).filter(User.line_user_id == user_id).first()
    if not admin or admin.role.value != "admin":
        return {"error": "管理者権限が必要です。"}

    target_line_id = params["target_user_id"]
    approve = params["approve"]

    target = db.query(User).filter(User.line_user_id == target_line_id).first()
    if not target:
        return {"error": "対象ユーザーが見つかりません。"}

    if approve:
        target.status = UserStatus.approved
        target.approved_at = datetime.now(timezone.utc)
        target.approved_by = admin.id
        msg = f"{target.line_display_name}さんを承認しました。"
    else:
        target.status = UserStatus.rejected
        target.rejection_reason = params.get("reason", "")
        msg = f"{target.line_display_name}さんを拒否しました。"

    db.commit()
    return {"status": "ok", "message": msg}


# ─── Handler registry ────────────────────────────────────────

_TOOL_HANDLERS = {
    "get_schedule": _handle_get_schedule,
    "find_available_slots": _handle_find_available_slots,
    "create_event": _handle_create_event,
    "update_event": _handle_update_event,
    "delete_event": _handle_delete_event,
    "get_emails": _handle_get_emails,
    "send_email_reply": _handle_send_email_reply,
    "set_email_filter": _handle_set_email_filter,
    "save_memo": _handle_save_memo,
    "search_memo": _handle_search_memo,
    "delete_memo": _handle_delete_memo,
    "register_unreplied": _handle_register_unreplied,
    "list_unreplied": _handle_list_unreplied,
    "complete_unreplied": _handle_complete_unreplied,
    "approve_user": _handle_approve_user,
}


def _build_approval_description(tool_name: str, tool_input: dict) -> str:
    """承認リクエストの説明文を生成。"""
    descriptions = {
        "create_event": lambda p: (
            f"予定を作成します:\n"
            f"  タイトル: {p.get('title', '')}\n"
            f"  日時: {p.get('date', '')} {p.get('start_time', '')}〜{p.get('end_time', '')}\n"
            f"  場所: {p.get('location', '未設定')}"
        ),
        "delete_event": lambda p: f"予定（ID: {p.get('event_id', '')}）を削除します。",
        "send_email_reply": lambda p: (
            f"メール（ID: {p.get('email_id', '')}）に返信します:\n"
            f"  本文: {p.get('body', '')[:100]}"
        ),
        "approve_user": lambda p: (
            f"ユーザー（ID: {p.get('target_user_id', '')}）を"
            f"{'承認' if p.get('approve') else '拒否'}します。"
        ),
    }
    builder = descriptions.get(tool_name)
    if builder:
        return builder(tool_input)
    return f"ツール {tool_name} を実行します。"
