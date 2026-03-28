"""LINE ↔ Agent ブリッジ - LINEメッセージとエージェントを接続"""

import json
import logging

from sqlalchemy.orm import Session

from src.ai.agent_orchestrator import run_agent_collect
from src.ai.shortcuts import apply_shortcut
from src.ai.tool_dispatcher import dispatch
from src.services.line_service import line_service

logger = logging.getLogger(__name__)

# インメモリ会話履歴（本番ではRedis等に移行）
_line_conversation_store: dict[str, list[dict]] = {}

# 保留中の承認リクエスト
_pending_approvals: dict[str, dict] = {}

MAX_LINE_MESSAGE_LENGTH = 5000
MAX_HISTORY_MESSAGES = 10


async def handle_line_message(
    user_id: str,
    message_text: str,
    reply_token: str,
    db: Session,
) -> None:
    """LINEメッセージを受け取り、エージェント経由で応答を返す。

    Args:
        user_id: LINE user ID
        message_text: ユーザーのメッセージテキスト
        reply_token: LINEリプライトークン
        db: データベースセッション
    """
    # ショートカット検出
    enhanced_message = apply_shortcut(message_text)

    # 会話履歴取得
    history = _line_conversation_store.get(user_id, [])

    try:
        # エージェント実行（一括取得モード）
        response_text, approval_requests = await run_agent_collect(
            user_message=enhanced_message,
            user_id=user_id,
            conversation_history=history,
            db_session=db,
        )

        # 会話履歴更新
        _update_line_history(user_id, message_text, response_text)

        # 承認リクエストがある場合
        if approval_requests:
            await _handle_approval_requests(user_id, reply_token, response_text, approval_requests)
            return

        # 通常応答
        if response_text:
            truncated = _truncate_for_line(response_text)
            await line_service.reply_text(reply_token, truncated)
        else:
            await line_service.reply_text(reply_token, "申し訳ありません。応答を生成できませんでした。")

    except Exception:
        logger.exception("Agent execution failed for LINE user %s", user_id)
        await line_service.reply_text(
            reply_token,
            "申し訳ありません。処理中にエラーが発生しました。しばらくしてから再度お試しください。",
        )


async def handle_line_postback_approval(
    user_id: str,
    reply_token: str,
    action: str,
    approval_id: str,
    db: Session,
) -> None:
    """LINE Postbackによる承認/拒否を処理する。

    Args:
        user_id: LINE user ID
        reply_token: LINEリプライトークン
        action: "approve" or "reject"
        approval_id: 承認リクエストID
        db: データベースセッション
    """
    key = f"{user_id}:{approval_id}"
    pending = _pending_approvals.pop(key, None)

    if not pending:
        await line_service.reply_text(reply_token, "この承認リクエストは期限切れか、既に処理済みです。")
        return

    if action == "approve":
        # 承認: ツールを実際に実行
        try:
            result = await dispatch(
                tool_name=pending["tool_name"],
                tool_input=pending["tool_input"],
                user_id=user_id,
                db=db,
                force_execute=True,
            )
            if isinstance(result, dict) and result.get("error"):
                await line_service.reply_text(reply_token, f"実行エラー: {result['error']}")
            else:
                message = result.get("message", "実行が完了しました。") if isinstance(result, dict) else "実行完了"
                await line_service.reply_text(reply_token, f"承認しました。\n{message}")
        except Exception:
            logger.exception("Approved tool execution failed")
            await line_service.reply_text(reply_token, "承認後の実行中にエラーが発生しました。")
    else:
        await line_service.reply_text(reply_token, "キャンセルしました。")


async def _handle_approval_requests(
    user_id: str,
    reply_token: str,
    response_text: str,
    approval_requests: list[dict],
) -> None:
    """承認リクエストをFlex Messageとして送信。"""
    messages = []

    # テキスト応答がある場合
    if response_text:
        messages.append(line_service.create_text_message(_truncate_for_line(response_text)))

    # 各承認リクエストに対してFlex Message作成
    for i, req in enumerate(approval_requests):
        approval_id = f"apr_{i}_{hash(json.dumps(req, sort_keys=True)) % 10000:04d}"
        key = f"{user_id}:{approval_id}"
        _pending_approvals[key] = {
            "tool_name": req.get("tool_name", ""),
            "tool_input": req.get("tool_input", {}),
        }

        description = req.get("description", "操作の実行確認")
        flex_contents = _build_approval_flex(description, approval_id)
        messages.append(
            line_service.create_flex_message(
                alt_text=f"確認: {description[:30]}",
                contents=flex_contents,
            )
        )

    if messages:
        await line_service.reply_message(reply_token, messages[:5])  # LINE上限5メッセージ


def _build_approval_flex(description: str, approval_id: str) -> dict:
    """承認用Flex Message (Bubble)を構築。"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "確認が必要です",
                    "weight": "bold",
                    "size": "md",
                    "color": "#1DB446",
                }
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": description[:200],
                    "wrap": True,
                    "size": "sm",
                }
            ],
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "承認",
                        "data": f"action=agent_approve&approval_id={approval_id}",
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "postback",
                        "label": "キャンセル",
                        "data": f"action=agent_reject&approval_id={approval_id}",
                    },
                },
            ],
        },
    }


def _truncate_for_line(text: str) -> str:
    """LINEメッセージの文字数制限に合わせてテキストを切り詰める。"""
    if len(text) <= MAX_LINE_MESSAGE_LENGTH:
        return text
    return text[: MAX_LINE_MESSAGE_LENGTH - 3] + "..."


def _update_line_history(user_id: str, user_message: str, assistant_text: str) -> None:
    """LINE用会話履歴を更新。"""
    if user_id not in _line_conversation_store:
        _line_conversation_store[user_id] = []

    history = _line_conversation_store[user_id]
    history.append({"role": "user", "content": user_message})
    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text})

    # 履歴上限
    if len(history) > MAX_HISTORY_MESSAGES * 2:
        _line_conversation_store[user_id] = history[-(MAX_HISTORY_MESSAGES * 2) :]
