"""エージェントオーケストレータ - Claude Tool Use自律ループ"""

import json
import logging
from collections.abc import AsyncGenerator

import anthropic

from src.ai.system_prompt import SYSTEM_PROMPT
from src.ai.tool_definitions import TOOL_DEFINITIONS
from src.ai.tool_dispatcher import ApprovalRequest, dispatch
from src.config import config

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5-20250514"
MAX_TURNS = 10
MAX_TOKENS = 4096


def _make_sse_event(event_type: str, data: dict | str) -> str:
    """SSEイベント文字列を生成。"""
    if isinstance(data, str):
        payload = json.dumps({"type": event_type, "content": data}, ensure_ascii=False)
    else:
        data["type"] = event_type
        payload = json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


async def run_agent(
    user_message: str,
    user_id: str,
    conversation_history: list[dict],
    db_session,
) -> AsyncGenerator[str, None]:
    """エージェントを実行し、SSEイベントを非同期に生成する。

    Args:
        user_message: ユーザーからのメッセージ
        user_id: LINE user ID
        conversation_history: 過去の会話履歴（Anthropic messages形式）
        db_session: SQLAlchemy Session

    Yields:
        SSEイベント文字列
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # 会話履歴にユーザーメッセージを追加
    messages = list(conversation_history)
    messages.append({"role": "user", "content": user_message})

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        logger.info("Agent turn %d/%d for user %s", turn, MAX_TURNS, user_id)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIError as e:
            logger.exception("Anthropic API error")
            yield _make_sse_event("error", f"AI APIエラーが発生しました: {str(e)}")
            yield _make_sse_event("done", "")
            return

        # レスポンスのcontent blockを処理
        assistant_content = response.content
        has_tool_use = False
        tool_results = []

        for block in assistant_content:
            if block.type == "text":
                if block.text:
                    yield _make_sse_event("text", block.text)

            elif block.type == "tool_use":
                has_tool_use = True
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id

                yield _make_sse_event("tool_start", {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                })

                # ツール実行
                try:
                    result = await dispatch(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        user_id=user_id,
                        db=db_session,
                    )
                except Exception as e:
                    logger.exception("Tool dispatch error: %s", tool_name)
                    result = {"error": f"ツール実行エラー: {str(e)}"}

                # 承認リクエストの場合
                if isinstance(result, ApprovalRequest):
                    yield _make_sse_event("approval_request", result.to_dict())
                    # 承認待ちとしてツール結果を返す
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps({
                            "status": "approval_required",
                            "description": result.description,
                            "message": "ユーザーの承認を待っています。承認されるまで実行を保留します。",
                        }, ensure_ascii=False),
                    })
                    yield _make_sse_event("tool_end", {
                        "tool_name": tool_name,
                        "status": "approval_required",
                    })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                    yield _make_sse_event("tool_end", {
                        "tool_name": tool_name,
                        "status": "ok" if "error" not in result else "error",
                    })

        # アシスタントメッセージを会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": [_block_to_dict(b) for b in assistant_content],
        })

        # ツール結果がある場合、会話を続行
        if has_tool_use and tool_results:
            messages.append({
                "role": "user",
                "content": tool_results,
            })
        else:
            # ツール使用なし = 最終応答完了
            break

        # stop_reason が end_turn ならループ終了
        if response.stop_reason == "end_turn" and not has_tool_use:
            break

    yield _make_sse_event("done", "")


async def run_agent_collect(
    user_message: str,
    user_id: str,
    conversation_history: list[dict],
    db_session,
) -> tuple[str, list[dict]]:
    """エージェントを実行し、テキスト結果と承認リクエストを集約して返す。

    LINE連携など、SSEではなく一括結果が必要な場合に使用。

    Returns:
        (応答テキスト, 承認リクエストのリスト)
    """
    text_parts: list[str] = []
    approval_requests: list[dict] = []

    async for sse_event in run_agent(user_message, user_id, conversation_history, db_session):
        # SSEイベントをパース
        if not sse_event.startswith("data: "):
            continue
        try:
            data = json.loads(sse_event.removeprefix("data: ").strip())
        except json.JSONDecodeError:
            continue

        event_type = data.get("type", "")
        if event_type == "text":
            text_parts.append(data.get("content", ""))
        elif event_type == "approval_request":
            approval_requests.append(data)
        elif event_type == "error":
            text_parts.append(f"[エラー] {data.get('content', '')}")

    return "".join(text_parts), approval_requests


def _block_to_dict(block) -> dict:
    """Anthropic content blockをdict形式に変換。"""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    return {"type": block.type}
