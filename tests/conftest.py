"""pytest設定とフィクスチャー"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPIテストクライアントのフィクスチャー"""
    return TestClient(app)
