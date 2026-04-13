"""FastAPI統合テスト"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Diary Companion API"
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_health_endpoint(client: TestClient) -> None:
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_cors_headers(client: TestClient) -> None:
    """CORS設定のテスト"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORSヘッダーの存在を確認
    assert "access-control-allow-origin" in response.headers


def test_invalid_endpoint(client: TestClient) -> None:
    """存在しないエンドポイントのテスト"""
    response = client.get("/nonexistent")
    assert response.status_code == 404