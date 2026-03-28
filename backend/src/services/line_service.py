"""LINE Messaging APIユーティリティ"""

import logging

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)

from src.config import config

logger = logging.getLogger(__name__)


class LineService:
    """LINE Messaging API操作をまとめるサービスクラス。"""

    def __init__(self):
        self._configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)

    def _get_api(self) -> MessagingApi:
        """MessagingApi インスタンスを生成。"""
        client = ApiClient(self._configuration)
        return MessagingApi(client)

    async def reply_message(self, reply_token: str, messages: list) -> None:
        """リプライトークンを使ってメッセージ返信。"""
        try:
            api = self._get_api()
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=messages,
                )
            )
            logger.info("Reply sent (token=%s...)", reply_token[:10])
        except Exception:
            logger.exception("Failed to send reply message")
            raise

    async def reply_text(self, reply_token: str, text: str) -> None:
        """テキストメッセージを返信（ショートカット）。"""
        msg = self.create_text_message(text)
        await self.reply_message(reply_token, [msg])

    async def push_message(self, user_id: str, messages: list) -> None:
        """ユーザーIDを指定してプッシュメッセージ送信。"""
        try:
            api = self._get_api()
            api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=messages,
                )
            )
            logger.info("Push message sent to %s", user_id)
        except Exception:
            logger.exception("Failed to push message to %s", user_id)
            raise

    async def push_text(self, user_id: str, text: str) -> None:
        """テキストメッセージをプッシュ送信（ショートカット）。"""
        msg = self.create_text_message(text)
        await self.push_message(user_id, [msg])

    def create_text_message(self, text: str) -> TextMessage:
        """テキストメッセージオブジェクトを生成。"""
        return TextMessage(text=text)

    def create_flex_message(self, alt_text: str, contents: dict) -> FlexMessage:
        """Flex Messageオブジェクトを生成。

        Args:
            alt_text: 通知やトーク一覧で表示される代替テキスト
            contents: Flex Message JSON (bubble/carousel)
        """
        return FlexMessage(
            alt_text=alt_text,
            contents=FlexContainer.from_dict(contents),
        )


# シングルトンインスタンス
line_service = LineService()
