"""FastAPI アプリケーションエントリーポイント"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes import auth, characters  # noqa: E402

app = FastAPI(
    title="AI Diary Companion",
    description="会話から自動生成される日記サービス",
    version="0.1.0",
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
