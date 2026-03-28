"""LINE AI Secretary - Backend Application"""

import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import config
from src.api.line_webhook import router as line_webhook_router
from src.api.auth import router as auth_router
from src.api.memo import router as memo_router
from src.api.unreplied import router as unreplied_router
from src.api.schedule import router as schedule_router
from src.api.email import router as email_router
from src.api.chat import router as chat_router
from src.api.scheduler import router as scheduler_router
from src.api.notifications import router as notifications_router
from src.api.admin import router as admin_router
from src.utils.audit_middleware import AuditLogMiddleware
from src.utils.error_handler import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LINE AI Secretary API",
    version="0.1.0",
)

# Error handlers
register_error_handlers(app)

# Middleware (order matters: last added = first executed)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(line_webhook_router)
app.include_router(auth_router)
app.include_router(memo_router)
app.include_router(unreplied_router)
app.include_router(schedule_router)
app.include_router(email_router)
app.include_router(chat_router)
app.include_router(scheduler_router)
app.include_router(notifications_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Graceful shutdown
def _shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, exiting...")
    sys.exit(0)


signal.signal(signal.SIGTERM, _shutdown_handler)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=config.HOST, port=config.PORT, reload=True)
