"""LINE Webhook endpoint - メッセージ受信・署名検証・イベントルーティング"""

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    FollowEvent,
    UnfollowEvent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
    ImageMessageContent,
    AudioMessageContent,
)

from src.config import config
from src.models.database import SessionLocal
from src.services.agent_line_bridge import handle_line_message, handle_line_postback_approval
from src.services.line_service import line_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/line", tags=["LINE Webhook"])

parser = WebhookParser(channel_secret=config.LINE_CHANNEL_SECRET)


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
):
    """LINE Webhook受信エンドポイント。署名検証後にイベントをルーティング。"""
    body = await request.body()
    body_text = body.decode("utf-8")

    # 署名検証
    try:
        events = parser.parse(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # イベントルーティング
    for event in events:
        try:
            await _route_event(event)
        except Exception:
            logger.exception("Error handling LINE event: %s", type(event).__name__)

    return {"status": "ok"}


async def _route_event(event) -> None:
    """イベント種別に応じたハンドラへルーティング。"""
    if isinstance(event, MessageEvent):
        await _handle_message_event(event)
    elif isinstance(event, FollowEvent):
        await _handle_follow_event(event)
    elif isinstance(event, UnfollowEvent):
        await _handle_unfollow_event(event)
    elif isinstance(event, PostbackEvent):
        await _handle_postback_event(event)
    else:
        logger.info("Unhandled event type: %s", type(event).__name__)


async def _handle_message_event(event: MessageEvent) -> None:
    """メッセージイベント処理。テキスト・画像・音声を振り分け。"""
    user_id = event.source.user_id
    reply_token = event.reply_token

    if isinstance(event.message, TextMessageContent):
        text = event.message.text
        logger.info("Text message from %s: %s", user_id, text[:50])
        # エージェント経由で応答
        db = SessionLocal()
        try:
            await handle_line_message(user_id, text, reply_token, db)
        finally:
            db.close()

    elif isinstance(event.message, ImageMessageContent):
        logger.info("Image message from %s", user_id)
        await line_service.reply_text(reply_token, "画像を受け取りました。解析中です...")

    elif isinstance(event.message, AudioMessageContent):
        logger.info("Audio message from %s", user_id)
        await line_service.reply_text(reply_token, "音声を受け取りました。文字起こし中です...")

    else:
        logger.info("Unsupported message type from %s: %s", user_id, type(event.message).__name__)
        await line_service.reply_text(reply_token, "このメッセージ形式には対応していません。")


async def _handle_follow_event(event: FollowEvent) -> None:
    """友だち追加イベント。ウェルカムメッセージ送信。"""
    user_id = event.source.user_id
    reply_token = event.reply_token
    logger.info("New follower: %s", user_id)

    welcome_text = (
        "LINE AI Secretaryへようこそ！\n\n"
        "このアシスタントは、あなたの日々の業務を効率化します。\n\n"
        "【主な機能】\n"
        "📅 予定管理\n"
        "📝 メモ・タスク管理\n"
        "📧 メール要約\n"
        "⏰ リマインダー\n\n"
        "ご利用には管理者の承認が必要です。\n"
        "承認後に全機能が有効になります。"
    )
    await line_service.reply_text(reply_token, welcome_text)
    # TODO: ユーザー仮登録 → 管理者承認フローへ


async def _handle_unfollow_event(event: UnfollowEvent) -> None:
    """ブロック・友だち解除イベント。"""
    user_id = event.source.user_id
    logger.info("Unfollowed by: %s", user_id)
    # TODO: ユーザーステータスを無効化


async def _handle_postback_event(event: PostbackEvent) -> None:
    """Postbackイベント（Rich Menu・Flex Messageボタン）。"""
    user_id = event.source.user_id
    reply_token = event.reply_token
    data = event.postback.data
    logger.info("Postback from %s: %s", user_id, data)

    # action=xxx&param=yyy 形式のパース
    params = dict(pair.split("=", 1) for pair in data.split("&") if "=" in pair)
    action = params.get("action", "")

    if action == "agent_approve" or action == "agent_reject":
        approval_id = params.get("approval_id", "")
        db = SessionLocal()
        try:
            await handle_line_postback_approval(
                user_id=user_id,
                reply_token=reply_token,
                action="approve" if action == "agent_approve" else "reject",
                approval_id=approval_id,
                db=db,
            )
        finally:
            db.close()
    elif action == "schedule":
        await line_service.reply_text(reply_token, "予定を確認しています...")
        # TODO: スケジュール取得処理
    elif action == "memo":
        await line_service.reply_text(reply_token, "メモを追加します。内容を入力してください。")
    elif action == "task":
        await line_service.reply_text(reply_token, "タスク一覧を取得しています...")
        # TODO: タスク取得処理
    elif action == "remind":
        await line_service.reply_text(reply_token, "リマインダーを設定します。日時と内容を入力してください。")
    elif action == "email_summary":
        await line_service.reply_text(reply_token, "メール要約を取得しています...")
        # TODO: メール要約処理
    elif action == "settings":
        await line_service.reply_text(reply_token, "設定メニューを表示します...")
        # TODO: 設定Flex Message送信
    elif action == "approve":
        target_user_id = params.get("user_id", "")
        logger.info("Approval action for user: %s", target_user_id)
        await line_service.reply_text(reply_token, f"ユーザー {target_user_id} を承認しました。")
        # TODO: 承認処理
    elif action == "reject":
        target_user_id = params.get("user_id", "")
        logger.info("Rejection action for user: %s", target_user_id)
        await line_service.reply_text(reply_token, f"ユーザー {target_user_id} を拒否しました。")
        # TODO: 拒否処理
    else:
        logger.warning("Unknown postback action: %s", action)
        await line_service.reply_text(reply_token, "不明なアクションです。")
