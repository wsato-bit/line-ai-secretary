"""SSEストリーミングチャットエンドポイント"""

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.ai.agent_orchestrator import run_agent
from src.ai.shortcuts import apply_shortcut
from src.models.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# インメモリ会話履歴（本番ではRedis等に移行）
_conversation_store: dict[str, list[dict]] = {}

MAX_HISTORY_MESSAGES = 20


class ChatRequest(BaseModel):
    """チャットリクエスト。"""
    message: str
    user_id: str


class ChatHistoryResponse(BaseModel):
    """会話履歴レスポンス。"""
    user_id: str
    messages: list[dict]


@router.post("")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """SSEストリーミングでエージェント応答を返す。"""
    user_id = request.user_id
    message = request.message

    if not message.strip():
        raise HTTPException(status_code=400, detail="メッセージが空です。")

    # ショートカット検出・ヒント付加
    enhanced_message = apply_shortcut(message)

    # 会話履歴取得
    history = _conversation_store.get(user_id, [])

    async def event_generator() -> AsyncGenerator[str, None]:
        collected_assistant_text = []
        try:
            async for sse_event in run_agent(
                user_message=enhanced_message,
                user_id=user_id,
                conversation_history=history,
                db_session=db,
            ):
                # テキストイベントを収集（履歴用）
                if sse_event.startswith("data: "):
                    try:
                        data = json.loads(sse_event.removeprefix("data: ").strip())
                        if data.get("type") == "text":
                            collected_assistant_text.append(data.get("content", ""))
                    except json.JSONDecodeError:
                        pass

                yield sse_event
        except Exception:
            logger.exception("Agent streaming error for user %s", user_id)
            yield f"data: {json.dumps({'type': 'error', 'content': '処理中にエラーが発生しました。'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'content': ''}, ensure_ascii=False)}\n\n"

        # 会話履歴を更新
        _update_history(user_id, message, "".join(collected_assistant_text))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str):
    """会話履歴を取得する。"""
    history = _conversation_store.get(user_id, [])
    return ChatHistoryResponse(user_id=user_id, messages=history)


@router.delete("/history")
async def clear_chat_history(user_id: str):
    """会話履歴をクリアする。"""
    _conversation_store.pop(user_id, None)
    return {"status": "ok", "message": "会話履歴をクリアしました。"}


def _update_history(user_id: str, user_message: str, assistant_text: str) -> None:
    """会話履歴を更新する。"""
    if user_id not in _conversation_store:
        _conversation_store[user_id] = []

    history = _conversation_store[user_id]
    history.append({"role": "user", "content": user_message})

    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text})

    # 履歴の上限管理
    if len(history) > MAX_HISTORY_MESSAGES * 2:
        _conversation_store[user_id] = history[-(MAX_HISTORY_MESSAGES * 2):]
