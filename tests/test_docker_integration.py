"""Docker環境固有のインテグレーションテスト

このテストはDocker Compose環境での動作を検証します。
環境変数の設定とデータベース接続の確認を行います。
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.main import app


class TestDockerEnvironment:
    """Docker環境の設定を検証するテスト"""

    def test_environment_variables_are_set(self) -> None:
        """必要な環境変数が設定されていることを確認"""
        # 必須環境変数のリスト
        required_vars = [
            "SECRET_KEY",
            "GROQ_API_KEY",
        ]

        for var in required_vars:
            assert os.getenv(var) is not None, f"環境変数 {var} が設定されていません"

    def test_database_url_format(self) -> None:
        """DATABASE_URLが正しい形式であることを確認"""
        database_url = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
        assert database_url is not None, "DATABASE_URLまたはASYNC_DATABASE_URLが設定されていません"
        assert database_url.startswith(
            "postgresql"
        ), "DATABASE_URLはpostgresqlで始まる必要があります"

    @pytest.mark.asyncio
    async def test_database_connection(self) -> None:
        """データベース接続が確立できることを確認

        このテストはASYNC_DATABASE_URLまたはDATABASE_URLを使用して
        実際のデータベースに接続します。
        """
        database_url = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URLが設定されていないためスキップ")

        # テスト用のエンジンを作成
        engine = create_async_engine(database_url, echo=False)

        try:
            async with engine.begin() as conn:
                # シンプルなクエリを実行して接続確認
                result = await conn.execute(text("SELECT 1"))
                row = result.fetchone()
                assert row is not None
                assert row[0] == 1
        finally:
            await engine.dispose()


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """ヘルスチェックエンドポイントが200を返すことを確認"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_correct_format(self, client: TestClient) -> None:
        """ヘルスチェックエンドポイントが正しい形式を返すことを確認"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestDockerDatabaseURL:
    """Docker環境でのDATABASE_URL設定を検証"""

    def test_database_url_uses_postgres_host_in_docker(self) -> None:
        """Docker環境ではpostgresホストを使用することを確認

        CI環境やローカル環境では異なるホストを使用する可能性があるため、
        環境変数CI_ENVIRONMENTが設定されている場合のみチェックします。
        """
        if os.getenv("ENVIRONMENT") != "development":
            pytest.skip("開発環境以外ではスキップ")

        database_url = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URLが設定されていないためスキップ")

        # Docker Compose環境ではpostgresホストを使用する
        # ローカル開発ではlocalhostも許可
        assert (
            "@postgres:" in database_url or "@localhost:" in database_url
        ), "DATABASE_URLのホストはpostgresまたはlocalhostである必要があります"
