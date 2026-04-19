# Docker開発環境セットアップガイド

## 概要

AI Diary CompanionプロジェクトはDockerを使用して開発環境を構築します。
これにより、ローカル環境に依存せず、一貫した開発環境を提供します。

## 必要条件

- Docker Desktop (最新版)
- Docker Compose (Docker Desktopに含まれています)

## セットアップ手順

### 1. 環境変数の設定

`.env.example`から`.env`ファイルを作成します：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、必要なAPIキーを設定：

```env
# Groq API Key（LLM機能を使用する場合）
GROQ_API_KEY=your-actual-groq-api-key

# JWT Secret Key（自動生成可能）
SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Dockerコンテナの起動

```bash
# すべてのサービスを起動（PostgreSQL + pgAdmin + FastAPI）
docker compose up

# バックグラウンドで起動
docker compose up -d

# 初回起動時（イメージのビルドが必要）
docker compose up --build
```

起動されるサービス:

- **postgres**: PostgreSQL 17データベース
- **pgadmin**: pgAdmin管理UI
- **app**: FastAPIバックエンドアプリケーション

### 3. データベースマイグレーション（初回のみ）

```bash
# マイグレーションの実行
docker compose exec app alembic upgrade head
```

### 4. アクセス確認

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)

## 開発時の操作

### コンテナの操作

```bash
# ログの確認
docker compose logs -f app

# 特定のサービスのログを見る
docker compose logs -f postgres

# コンテナに入る
docker compose exec app bash

# PostgreSQLに接続
docker compose exec postgres psql -U postgres -d ai_diary_companion
```

### コードの変更

- `app/`ディレクトリ内のコードを変更すると、自動的にリロードされます
- `pyproject.toml`を変更した場合は、イメージの再ビルドが必要です：
  ```bash
  docker compose build app
  docker compose up
  ```

### テストの実行

```bash
# コンテナ内でテストを実行
docker compose exec app pytest

# カバレッジレポート付き
docker compose exec app pytest --cov=app --cov-report=html
```

### データベース操作

```bash
# データベースに接続
docker compose exec postgres psql -U postgres -d ai_diary_companion

# テストデータベースに接続
docker compose exec postgres psql -U postgres -d ai_diary_companion_test

# データベースのバックアップ
docker compose exec postgres pg_dump -U postgres ai_diary_companion > backup.sql

# データベースのリストア
docker compose exec -T postgres psql -U postgres ai_diary_companion < backup.sql
```

## クリーンアップ

```bash
# コンテナを停止
docker compose down

# コンテナとボリュームを削除（データも削除される）
docker compose down -v

# イメージも含めて完全削除
docker compose down -v --rmi all
```

## トラブルシューティング

### ポートが既に使用されている

```bash
# ポート8000が使用中の場合
lsof -i :8000
# プロセスをkillするか、docker compose.ymlでポートを変更

# ポート5432が使用中の場合
lsof -i :5432
# ローカルのPostgreSQLが起動している可能性があります
```

### コンテナが起動しない

```bash
# ログを確認
docker compose logs app

# イメージを再ビルド
docker compose build --no-cache app
docker compose up
```

### データベース接続エラー

```bash
# PostgreSQLコンテナの状態を確認
docker compose ps postgres

# ヘルスチェックのステータスを確認
docker compose ps

# データベースを再作成
docker compose down -v
docker compose up
```

## Docker環境の構成

### サービス構成

| サービス名 | イメージ               | ポート | 説明                   |
| ---------- | ---------------------- | ------ | ---------------------- |
| postgres   | postgres:17-alpine     | 5432   | PostgreSQLデータベース |
| pgadmin    | dpage/pgadmin4:latest  | 5050   | データベース管理UI     |
| app        | (Dockerfileからビルド) | 8000   | FastAPIバックエンド    |

### 使用イメージ

- **Python**: python:3.13-slim (アプリケーション)
- **PostgreSQL**: postgres:17-alpine (データベース)
- **pgAdmin**: dpage/pgadmin4:latest (管理UI)

### ボリューム

- `postgres_data`: PostgreSQLのデータ永続化
- `./app:/app/app`: アプリケーションコード（ホットリロード対応）
- `./alembic:/app/alembic`: マイグレーションファイル
- `./scripts:/app/scripts`: スクリプトファイル

### ネットワーク

- `ai_diary_network`: 内部通信用ブリッジネットワーク
  - コンテナ間通信では、サービス名（`postgres`, `app`）をホスト名として使用

### 環境変数

Docker Compose内で自動設定される環境変数：

- `DATABASE_URL`: PostgreSQL接続URL（コンテナ間通信では`postgres:5432`を使用）
- `ASYNC_DATABASE_URL`: 非同期接続URL
- `SECRET_KEY`: JWT署名用秘密鍵
- `GROQ_API_KEY`: Groq API認証キー
- `CORS_ORIGINS`: CORS許可オリジン

## 本番環境への注意事項

本番環境では以下の点を変更してください：

1. `.env`ファイルの`SECRET_KEY`を強力なランダム値に変更
2. `docker compose.yml`の`DEBUG`を`false`に設定
3. PostgreSQLの`POSTGRES_PASSWORD`を強力なパスワードに変更
4. ボリュームのバックアップ戦略を策定
5. HTTPSの設定（リバースプロキシ等）
