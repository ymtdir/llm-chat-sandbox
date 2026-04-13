#!/bin/bash

# Docker環境統合テストスクリプト

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "====================================="
echo "Docker環境統合テスト"
echo "====================================="
echo ""

# テスト結果を追跡
TESTS_PASSED=0
TESTS_FAILED=0

# テスト関数
test_case() {
    local test_name=$1
    local test_command=$2
    local expected_result=$3

    echo -n "Testing: $test_name ... "

    if eval "$test_command"; then
        if [ "$expected_result" = "pass" ]; then
            echo -e "${GREEN}PASSED${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAILED${NC} (expected to fail)"
            ((TESTS_FAILED++))
        fi
    else
        if [ "$expected_result" = "fail" ]; then
            echo -e "${GREEN}PASSED${NC} (correctly failed)"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAILED${NC}"
            ((TESTS_FAILED++))
        fi
    fi
}

echo "1. Docker環境の起動テスト"
echo "-------------------------"

# Docker Composeでサービスを起動
echo "Starting Docker containers..."
docker compose down -v 2>/dev/null || true
docker compose up -d --build

# PostgreSQLの起動を待つ
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U postgres &>/dev/null; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}PostgreSQL failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# FastAPIの起動を待つ
echo "Waiting for FastAPI to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        echo -e "${GREEN}FastAPI is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}FastAPI failed to start${NC}"
        exit 1
    fi
    sleep 1
done

echo ""
echo "2. APIエンドポイントテスト"
echo "-------------------------"

# ヘルスチェックエンドポイント
test_case "Health check endpoint" \
    "curl -s http://localhost:8000/health | grep -q '\"status\":\"healthy\"'" \
    "pass"

# ルートエンドポイント
test_case "Root endpoint" \
    "curl -s http://localhost:8000/ | grep -q '\"message\":\"AI Diary Companion API\"'" \
    "pass"

# APIバージョンチェック
test_case "API version check" \
    "curl -s http://localhost:8000/ | grep -q '\"version\":\"0.1.0\"'" \
    "pass"

echo ""
echo "3. データベース接続テスト"
echo "-------------------------"

# メインデータベースの存在確認
test_case "Main database exists" \
    "docker compose exec -T postgres psql -U postgres -lqt | grep -q ai_diary_companion" \
    "pass"

# テストデータベースの存在確認
test_case "Test database exists" \
    "docker compose exec -T postgres psql -U postgres -lqt | grep -q ai_diary_companion_test" \
    "pass"

# データベース接続テスト
test_case "Database connection" \
    "docker compose exec -T postgres psql -U postgres -d ai_diary_companion -c 'SELECT 1' &>/dev/null" \
    "pass"

echo ""
echo "4. ホットリロードテスト"
echo "-------------------------"

# app/main.pyを一時的に変更
echo "Modifying app/main.py to test hot-reload..."
cp app/main.py app/main.py.backup

# テスト用の変更を追加
cat >> app/main.py << 'EOF'

@app.get("/test-reload")
async def test_reload() -> dict[str, str]:
    """ホットリロードテスト用エンドポイント"""
    return {"message": "Hot reload works!"}
EOF

# ホットリロードを待つ
sleep 3

# 新しいエンドポイントをテスト
test_case "Hot reload functionality" \
    "curl -s http://localhost:8000/test-reload | grep -q '\"message\":\"Hot reload works!\"'" \
    "pass"

# ファイルを元に戻す
mv app/main.py.backup app/main.py

echo ""
echo "5. 環境変数テスト"
echo "-------------------------"

# CORS設定の環境変数テスト
test_case "CORS environment variable" \
    "docker compose exec -T app env | grep -q CORS_ORIGINS" \
    "pass"

# データベース環境変数テスト
test_case "Database URL environment variable" \
    "docker compose exec -T app env | grep -q DATABASE_URL" \
    "pass"

echo ""
echo "6. コンテナヘルスチェック"
echo "-------------------------"

# PostgreSQLコンテナのヘルス
test_case "PostgreSQL container health" \
    "docker compose ps postgres | grep -q 'healthy'" \
    "pass"

# アプリケーションコンテナのステータス
test_case "App container status" \
    "docker compose ps app | grep -q 'Up'" \
    "pass"

echo ""
echo "====================================="
echo "テスト結果サマリー"
echo "====================================="
echo -e "合格: ${GREEN}$TESTS_PASSED${NC}"
echo -e "失敗: ${RED}$TESTS_FAILED${NC}"

# クリーンアップ
echo ""
echo "Cleaning up..."
docker compose down

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ すべてのテストが合格しました！${NC}"
    exit 0
else
    echo -e "${RED}❌ $TESTS_FAILED 個のテストが失敗しました${NC}"
    exit 1
fi