# CLAUDE.md

## プロジェクト概要

AI Diary Companion - 会話から自動生成される日記サービス。
詳細は `docs/requirements.md` を参照。

## 技術スタック

- バックエンド: Python / FastAPI / SQLAlchemy (async)
- フロントエンド: TypeScript / React
- DB: PostgreSQL (async)
- 認証: JWT

詳細なバージョン情報は `docs/basic-design.md` を参照。

## アーキテクチャ

レイヤードアーキテクチャを採用:
`API (routes)` → `Services` → `Repositories` → `Models`

詳細は `docs/detailed-design.md` を参照。

## 開発ガイド

プロジェクト構造・命名規則・各レイヤーの責務は `docs/development-guide.md` を参照。

## デザインルール

デザインシステムの仕様は `DESIGN.md` を参照すること。UIを生成する際は必ずこのファイルのルールに従うこと。

## コマンド

```bash
# すべてのサービスを起動（PostgreSQL + pgAdmin + FastAPI）
docker compose up -d

# ログを確認
docker compose logs -f app

# バックエンドのみ再起動
docker compose restart app

# テスト実行
docker compose exec app pytest

# lint（コンテナ内）
docker compose exec app ruff check app/

# 型チェック（コンテナ内）
docker compose exec app mypy app/

# すべてのサービスを停止
docker compose down
```

## ドキュメント一覧

| ファイル                    | 内容                 |
| --------------------------- | -------------------- |
| `docs/requirements.md`      | 要件定義             |
| `docs/basic-design.md`      | 基本設計・技術選定   |
| `docs/detailed-design.md`   | 詳細設計・DB設計     |
| `docs/development-guide.md` | 開発ガイドライン     |
| `docs/DOCKER_SETUP.md`      | Docker環境構築手順   |
| `DESIGN.md`                 | デザインシステム仕様 |
