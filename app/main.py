"""FastAPI アプリケーションエントリーポイント"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes import auth, characters, conversations  # noqa: E402
from app.scheduler.jobs import process_pending_responses  # noqa: E402

logger = logging.getLogger(__name__)

# Scheduler instance
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager.

    Starts background scheduler on startup and shuts it down on shutdown.
    """
    # Startup
    logger.info("Starting AI response scheduler...")
    scheduler.add_job(
        process_pending_responses,
        "interval",
        minutes=1,
        id="process_pending_responses",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started successfully")

    yield

    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    logger.info("Scheduler shut down successfully")


app = FastAPI(
    title="AI Diary Companion",
    description="会話から自動生成される日記サービス",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS設定（環境変数から読み込み）
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """ルートエンドポイント - ヘルスチェック用"""
    return {
        "message": "AI Diary Companion API",
        "status": "ok",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router)
app.include_router(characters.router)
app.include_router(conversations.router)
