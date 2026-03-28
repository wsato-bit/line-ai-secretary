"""LINE Rich Menu 設定・作成ユーティリティ"""

import logging

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    RichMenuRequest,
    RichMenuSize,
    RichMenuArea,
    RichMenuBounds,
)
from linebot.v3.messaging.models import (
    PostbackAction,
)

from src.config import config

logger = logging.getLogger(__name__)


def create_rich_menu() -> RichMenuRequest:
    """6分割Rich Menuを定義。

    レイアウト（2行3列 = 2500x1686px）:
    +----------+----------+----------+
    | 予定確認  | メモ追加  | タスク管理 |
    +----------+----------+----------+
    | リマインド | メール要約 |  設定    |
    +----------+----------+----------+
    """
    col_w = 2500 // 3  # 833
    row_h = 1686 // 2  # 843

    areas = [
        # 上段左: 予定確認
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=col_w, height=row_h),
            action=PostbackAction(label="予定確認", data="action=schedule"),
        ),
        # 上段中: メモ追加
        RichMenuArea(
            bounds=RichMenuBounds(x=col_w, y=0, width=col_w, height=row_h),
            action=PostbackAction(label="メモ追加", data="action=memo"),
        ),
        # 上段右: タスク管理
        RichMenuArea(
            bounds=RichMenuBounds(x=col_w * 2, y=0, width=2500 - col_w * 2, height=row_h),
            action=PostbackAction(label="タスク管理", data="action=task"),
        ),
        # 下段左: リマインド
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=row_h, width=col_w, height=1686 - row_h),
            action=PostbackAction(label="リマインド", data="action=remind"),
        ),
        # 下段中: メール要約
        RichMenuArea(
            bounds=RichMenuBounds(x=col_w, y=row_h, width=col_w, height=1686 - row_h),
            action=PostbackAction(label="メール要約", data="action=email_summary"),
        ),
        # 下段右: 設定
        RichMenuArea(
            bounds=RichMenuBounds(x=col_w * 2, y=row_h, width=2500 - col_w * 2, height=1686 - row_h),
            action=PostbackAction(label="設定", data="action=settings"),
        ),
    ]

    return RichMenuRequest(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="LINE AI Secretary Menu",
        chat_bar_text="メニューを開く",
        areas=areas,
    )


async def setup_rich_menu() -> str | None:
    """Rich Menuを作成しデフォルトに設定する。

    Returns:
        作成されたRich Menu ID。失敗時はNone。
    """
    configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)

    try:
        client = ApiClient(configuration)
        api = MessagingApi(client)

        # Rich Menu作成
        rich_menu_request = create_rich_menu()
        result = api.create_rich_menu(rich_menu_request)
        rich_menu_id = result.rich_menu_id
        logger.info("Rich Menu created: %s", rich_menu_id)

        # TODO: Rich Menu画像アップロード
        # rich_menu_image_path = Path(__file__).parent.parent.parent / "assets" / "richmenu.png"
        # if rich_menu_image_path.exists():
        #     with open(rich_menu_image_path, "rb") as f:
        #         api.set_rich_menu_image(rich_menu_id, body=f.read(), content_type="image/png")

        # デフォルトRich Menuに設定
        api.set_default_rich_menu(rich_menu_id)
        logger.info("Rich Menu set as default: %s", rich_menu_id)

        return rich_menu_id

    except Exception:
        logger.exception("Failed to setup Rich Menu")
        return None
