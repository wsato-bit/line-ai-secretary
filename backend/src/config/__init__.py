import os
from pathlib import Path

from dotenv import load_dotenv

# .env.local を読み込み
env_path = Path(__file__).resolve().parent.parent.parent / ".env.local"
load_dotenv(env_path)


class Config:
    """環境変数を集約する設定クラス。"""

    # Server
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8293"))

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # Redis
    REDIS_URL: str = os.environ.get("REDIS_URL", "")

    # AI
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

    # LINE Messaging API
    LINE_CHANNEL_SECRET: str = os.environ.get("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN: str = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

    # LINE Login
    LINE_LOGIN_CHANNEL_ID: str = os.environ.get("LINE_LOGIN_CHANNEL_ID", "")
    LINE_LOGIN_CHANNEL_SECRET: str = os.environ.get("LINE_LOGIN_CHANNEL_SECRET", "")

    # Google
    GOOGLE_APPLICATION_CREDENTIALS: str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    GCS_BUCKET_NAME: str = os.environ.get("GCS_BUCKET_NAME", "")

    # Security
    ENCRYPTION_KEY: str = os.environ.get("ENCRYPTION_KEY", "")

    # Job Scheduler Auth
    JOB_AUTH_SECRET: str = os.environ.get("JOB_AUTH_SECRET", "")

    # CORS
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3847")


config = Config()
