#!/bin/bash
# 開発環境セットアップの検証スクリプト

set -e

echo "========================================="
echo "AI Diary Companion - 開発環境検証"
echo "========================================="
echo ""

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python バージョンチェック
echo "1. Python バージョンチェック"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} がインストールされています"
else
    echo -e "${RED}✗${NC} Python がインストールされていません"
    exit 1
fi

# Python 3.12以上かチェック
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo -e "${GREEN}✓${NC} Python 3.12以上が要件を満たしています"
else
    echo -e "${YELLOW}⚠${NC} Python 3.12以上を推奨します（現在: ${PYTHON_MAJOR}.${PYTHON_MINOR}）"
fi
echo ""

# Node.js バージョンチェック
echo "2. Node.js バージョンチェック"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js ${NODE_VERSION} がインストールされています"
else
    echo -e "${RED}✗${NC} Node.js がインストールされていません"
    exit 1
fi

# Node.js 22.x LTS以上かチェック
NODE_MAJOR=$(node -p 'process.versions.node.split(".")[0]')
if [ "$NODE_MAJOR" -ge 22 ]; then
    echo -e "${GREEN}✓${NC} Node.js 22.x LTS以上が要件を満たしています"
else
    echo -e "${YELLOW}⚠${NC} Node.js 22.x LTS以上を推奨します（現在: v${NODE_MAJOR}）"
fi
echo ""

# PostgreSQL バージョンチェック
echo "3. PostgreSQL バージョンチェック"
if command -v psql &> /dev/null; then
    POSTGRES_VERSION=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}✓${NC} PostgreSQL ${POSTGRES_VERSION} がインストールされています"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL がインストールされていません"
    echo "   インストール方法:"
    echo "   - macOS: brew install postgresql@17"
    echo "   - Ubuntu: sudo apt install postgresql-17"
fi
echo ""

# .env ファイルチェック
echo "4. 環境変数ファイルチェック"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env ファイルが存在します"
else
    echo -e "${YELLOW}⚠${NC} .env ファイルが存在しません"
    echo "   .env.example をコピーして .env を作成してください:"
    echo "   cp .env.example .env"
fi
echo ""

# Python依存関係チェック
echo "5. Python依存関係チェック"
if python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} FastAPI がインストールされています"
else
    echo -e "${RED}✗${NC} FastAPI がインストールされていません"
    echo "   依存関係をインストールしてください:"
    echo "   pip install -e \".[dev]\""
    exit 1
fi

if python3 -c "import sqlalchemy" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SQLAlchemy がインストールされています"
else
    echo -e "${RED}✗${NC} SQLAlchemy がインストールされていません"
    exit 1
fi

if python3 -c "import alembic" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Alembic がインストールされています"
else
    echo -e "${RED}✗${NC} Alembic がインストールされていません"
    exit 1
fi
echo ""

# ディレクトリ構造チェック
echo "6. ディレクトリ構造チェック"
REQUIRED_DIRS=("app" "docs" "alembic")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} ${dir}/ ディレクトリが存在します"
    else
        echo -e "${YELLOW}⚠${NC} ${dir}/ ディレクトリが存在しません"
    fi
done
echo ""

# 必須ファイルチェック
echo "7. 必須ファイルチェック"
REQUIRED_FILES=("pyproject.toml" ".env.example" "alembic.ini" "README.md" "app/main.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} ${file} が存在します"
    else
        echo -e "${RED}✗${NC} ${file} が存在しません"
    fi
done
echo ""

echo "========================================="
echo "検証完了！"
echo "========================================="
echo ""
echo "次のステップ:"
echo "1. .env ファイルを作成・編集する"
echo "2. PostgreSQL データベースを作成する"
echo "3. Alembic マイグレーションを実行する"
echo "4. FastAPI サーバーを起動する: uvicorn app.main:app --reload"
echo ""
