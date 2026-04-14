"""pytest設定とフィクスチャー"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPIテストクライアントのフィクスチャー"""
    return TestClient(app)
