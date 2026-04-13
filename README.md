# AI Diary Companion

会話から自動生成される日記サービス

## 概要

AI Diary Companionは、AIキャラクターとの自然な会話を通じて自動的に日記が生成されるサービスです。「日記を書く」という意識なく、日常会話を楽しむだけで記録が残る体験を提供します。

### 主な機能

- リアルな人間との会話体験（性格・職業・時間帯に応じた自然な返信タイミング）
- 柔軟なAIキャラクター設定（性別、関係性、性格、職業など）
- 1日の会話から自動生成される日記
- プッシュ通知機能

## 技術スタック

### バックエンド
- **言語**: Python 3.12
- **フレームワーク**: FastAPI 0.115+
- **データベース**: PostgreSQL 17.x
- **ORM**: SQLAlchemy 2.0 (async)
- **LLM**: Groq API (Llama 3.3 70B)
- **スケジューラー**: APScheduler
- **認証**: JWT (python-jose)

### フロントエンド
- **言語**: TypeScript
- **フレームワーク**: React
- **ランタイム**: Node.js 22.x LTS

### インフラ
- **プッシュ通知**: Firebase Cloud Messaging

## 開発環境セットアップ

### 前提条件

以下のソフトウェアがインストールされていることを確認してください：

- Python 3.12+
- Node.js 22.x LTS
- PostgreSQL 17.x
- Git

### セットアップ手順

#### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd llm-chat-sandbox
```

#### 2. Python環境の構築

```bash
# 仮想環境の作成
python3.12 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存関係のインストール
pip install -e ".[dev]"
```

#### 3. PostgreSQL データベースの準備

```bash
# PostgreSQLにログイン
psql -U postgres

# データベースの作成
CREATE DATABASE ai_diary_companion;
CREATE DATABASE ai_diary_companion_test;  -- テスト用

# ユーザーの作成（必要に応じて）
CREATE USER ai_diary_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ai_diary_companion TO ai_diary_user;
GRANT ALL PRIVILEGES ON DATABASE ai_diary_companion_test TO ai_diary_user;

# 終了
\q
```

#### 4. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集
# 以下の値を必ず設定してください：
# - DATABASE_URL: PostgreSQL接続URL
# - SECRET_KEY: JWT用シークレットキー (openssl rand -hex 32 で生成)
# - GROQ_API_KEY: Groq APIキー (https://console.groq.com/ から取得)
# - FIREBASE_CREDENTIALS_PATH: Firebase認証情報JSONファイルのパス
```

**重要な環境変数：**

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql+psycopg://postgres:postgres@localhost:5432/ai_diary_companion` |
| `SECRET_KEY` | JWT認証用シークレットキー | `openssl rand -hex 32` で生成 |
| `GROQ_API_KEY` | Groq API キー | https://console.groq.com/ から取得 |
| `FIREBASE_CREDENTIALS_PATH` | Firebase認証情報ファイルパス | `./firebase-credentials.json` |

#### 5. データベースマイグレーション

```bash
# Alembicの初期化（初回のみ）
alembic init alembic

# マイグレーションの実行
alembic upgrade head
```

#### 6. フロントエンドのセットアップ（今後実装）

```bash
cd frontend
npm install
```

### 開発サーバーの起動

#### バックエンド (FastAPI)

```bash
# 開発モードで起動（ホットリロード有効）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

アクセス先:
- API: http://localhost:8000
- API ドキュメント (Swagger UI): http://localhost:8000/docs
- API ドキュメント (ReDoc): http://localhost:8000/redoc

#### フロントエンド（今後実装）

```bash
cd frontend
npm run dev
```

アクセス先:
- フロントエンド: http://localhost:3000

## テスト

```bash
# すべてのテストを実行
pytest

# カバレッジレポート付きで実行
pytest --cov=app --cov-report=html

# 特定のテストファイルを実行
pytest tests/unit/services/test_conversation_service.py

# テストをウォッチモードで実行
pytest --watch
```

## コード品質チェック

```bash
# Ruffによるリント
ruff check .

# Ruffによる自動修正
ruff check --fix .

# Ruffによるフォーマット
ruff format .

# mypyによる型チェック
mypy app
```

## プロジェクト構造

```
llm-chat-sandbox/
├── app/                     # バックエンドアプリケーション（FastAPI）
│   ├── main.py              # エントリーポイント
│   ├── core/                # コア機能（設定、セキュリティ、DB）
│   ├── models/              # SQLAlchemyモデル（データレイヤー）
│   ├── schemas/             # Pydanticスキーマ（バリデーション）
│   ├── api/                 # APIレイヤー（routes, deps, websocket）
│   ├── services/            # サービスレイヤー（ビジネスロジック）
│   ├── domain/              # ドメインレイヤー（ドメインモデル）
│   ├── repositories/        # リポジトリ（データアクセス）
│   └── scheduler/           # スケジューラー（バックグラウンドジョブ）
├── alembic/                 # マイグレーション
├── tests/                   # テストコード
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── frontend/                # フロントエンド（React）
├── docs/                    # プロジェクトドキュメント
│   ├── requirements.md      # 要件定義書
│   ├── basic-design.md      # 基本設計書
│   ├── detailed-design.md   # 詳細設計書
│   └── development-guide.md # 開発ガイドライン
├── .env.example             # 環境変数テンプレート
├── pyproject.toml           # Python依存関係・設定
├── alembic.ini              # Alembic設定
└── README.md                # このファイル
```

## 開発ガイドライン

詳細な開発ガイドラインは [docs/development-guide.md](./docs/development-guide.md) を参照してください。

### コミットメッセージ規約

```
<type>: <subject>

<body>
```

**type:**
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `docs`: ドキュメント
- `test`: テスト追加・修正
- `chore`: ビルド、設定変更

### ブランチ戦略

- `main`: 本番リリース済みの安定版コードのみ
- `feature/*`: 新機能開発
- `fix/*`: バグ修正
- `refactor/*`: リファクタリング

## トラブルシューティング

### PostgreSQL接続エラー

```bash
# PostgreSQLが起動しているか確認
pg_isready

# PostgreSQLのステータス確認
# macOS (Homebrew):
brew services list
# Linux:
sudo systemctl status postgresql
```

### Python仮想環境のエラー

```bash
# 仮想環境を削除して再作成
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Alembicマイグレーションエラー

```bash
# マイグレーション履歴の確認
alembic history

# 現在のリビジョンを確認
alembic current

# 特定のリビジョンにダウングレード
alembic downgrade <revision>
```

## ライセンス

このプロジェクトはプロトタイプです。ライセンスは今後決定予定。

## 連絡先

プロジェクトに関する質問や提案は、GitHubのIssueで受け付けています。
