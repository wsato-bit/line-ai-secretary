"""LINE Login OAuth 認証エンドポイント"""

import logging
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel

from src.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# LINE Login OAuth endpoints
LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"
LINE_REVOKE_URL = "https://api.line.me/oauth2/v2.1/revoke"

# セッション内state管理（本番ではRedis等に移行）
_pending_states: dict[str, bool] = {}


class LoginResponse(BaseModel):
    authorization_url: str
    state: str


class CallbackResponse(BaseModel):
    user_id: str
    display_name: str
    picture_url: str | None = None
    status: str  # "active", "pending_approval", "new"
    access_token: str


class UserInfo(BaseModel):
    user_id: str
    display_name: str
    picture_url: str | None = None
    status: str


@router.get("/line/login", response_model=LoginResponse)
async def line_login(request: Request):
    """LINE Login認証URLを生成。"""
    state = secrets.token_urlsafe(32)
    _pending_states[state] = True

    callback_url = _get_callback_url(request)
    params = {
        "response_type": "code",
        "client_id": config.LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": callback_url,
        "state": state,
        "scope": "profile openid",
    }
    authorization_url = f"{LINE_AUTH_URL}?{urlencode(params)}"

    return LoginResponse(authorization_url=authorization_url, state=state)


@router.get("/line/callback", response_model=CallbackResponse)
async def line_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
):
    """LINE Login OAuthコールバック。認可コードをトークンに交換。"""
    # state検証（CSRF対策）
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    del _pending_states[state]

    callback_url = _get_callback_url(request)

    # 認可コード → アクセストークン交換
    token_data = await _exchange_code_for_token(code, callback_url)
    access_token = token_data.get("access_token")
    if not access_token:
        logger.error("Token exchange failed: %s", token_data)
        raise HTTPException(status_code=400, detail="Token exchange failed")

    # プロフィール取得
    profile = await _get_line_profile(access_token)
    user_id = profile.get("userId", "")
    display_name = profile.get("displayName", "")
    picture_url = profile.get("pictureUrl")

    if not user_id:
        raise HTTPException(status_code=400, detail="Failed to get user profile")

    # ユーザー登録/ステータス確認
    user_status = await _resolve_user_status(user_id, display_name, picture_url)

    logger.info("LINE Login success: user_id=%s, status=%s", user_id, user_status)

    return CallbackResponse(
        user_id=user_id,
        display_name=display_name,
        picture_url=picture_url,
        status=user_status,
        access_token=access_token,
    )


@router.post("/logout")
async def logout(response: Response):
    """ログアウト。セッション/トークン無効化。"""
    # TODO: Redis/DBからセッション削除
    logger.info("User logged out")
    return {"status": "ok", "message": "ログアウトしました"}


@router.get("/me", response_model=UserInfo)
async def get_current_user(request: Request):
    """現在のユーザー情報取得。"""
    # Authorization ヘッダーからトークン取得
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = auth_header.removeprefix("Bearer ").strip()

    # LINE APIでプロフィール取得（トークン有効性も検証）
    try:
        profile = await _get_line_profile(access_token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = profile.get("userId", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # TODO: DBからユーザーステータス取得
    return UserInfo(
        user_id=user_id,
        display_name=profile.get("displayName", ""),
        picture_url=profile.get("pictureUrl"),
        status="active",
    )


def _get_callback_url(request: Request) -> str:
    """コールバックURLを構築。"""
    return str(request.url_for("line_callback"))


async def _exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """認可コードをアクセストークンに交換。"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LINE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": config.LINE_LOGIN_CHANNEL_ID,
                "client_secret": config.LINE_LOGIN_CHANNEL_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            logger.error("LINE token exchange error: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        return resp.json()


async def _get_line_profile(access_token: str) -> dict:
    """LINE プロフィールAPI呼び出し。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            LINE_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            logger.error("LINE profile API error: %s", resp.status_code)
            raise HTTPException(status_code=401, detail="Failed to get LINE profile")
        return resp.json()


async def _resolve_user_status(user_id: str, display_name: str, picture_url: str | None) -> str:
    """ユーザー登録状況を解決。新規→仮登録、既存→ステータス返却。"""
    # TODO: DB検索で既存ユーザー確認
    # existing_user = await user_repo.get_by_line_user_id(user_id)
    # if existing_user:
    #     return existing_user.status  # "active" | "pending_approval" | "suspended"

    # 新規ユーザー: 仮登録して管理者承認待ちへ
    # TODO: DB登録
    # await user_repo.create(line_user_id=user_id, display_name=display_name, ...)
    logger.info("New user registered (pending approval): %s (%s)", user_id, display_name)
    return "pending_approval"
