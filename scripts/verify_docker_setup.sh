#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "====================================="
echo "AI Diary Companion - Docker Setup Verification"
echo "====================================="
echo ""

# Track overall status
ALL_PASSED=true

# Function to check command exists
check_command() {
    local cmd=$1
    local display_name=$2

    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} $display_name: $version"
        return 0
    else
        echo -e "${RED}✗${NC} $display_name: not found"
        ALL_PASSED=false
        return 1
    fi
}

echo "1. Docker Requirements"
echo "----------------------"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,$//')
    echo -e "${GREEN}✓${NC} Docker: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker: not installed"
    echo "  Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    ALL_PASSED=false
fi

# Check Docker Compose
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version | cut -d' ' -f4)
    echo -e "${GREEN}✓${NC} Docker Compose: $COMPOSE_VERSION"
else
    echo -e "${RED}✗${NC} Docker Compose: not found"
    ALL_PASSED=false
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker daemon: running"
else
    echo -e "${RED}✗${NC} Docker daemon: not running"
    echo "  Please start Docker Desktop"
    ALL_PASSED=false
fi

echo ""
echo "2. Project Files"
echo "----------------"

# Check required files
FILES=("Dockerfile" "docker compose.yml" ".dockerignore" "pyproject.toml" ".env.example")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file not found"
        ALL_PASSED=false
    fi
done

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check for required keys (without revealing values)
    source .env 2>/dev/null

    if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" != "your-secret-key-here-change-in-production" ]; then
        echo -e "${GREEN}✓${NC} SECRET_KEY: configured"
    else
        echo -e "${YELLOW}⚠${NC} SECRET_KEY: using default (change for production)"
    fi

    if [ -n "$GROQ_API_KEY" ] && [ "$GROQ_API_KEY" != "your-groq-api-key-here" ]; then
        echo -e "${GREEN}✓${NC} GROQ_API_KEY: configured"
    else
        echo -e "${YELLOW}⚠${NC} GROQ_API_KEY: not configured (required for LLM features)"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo "  Run: cp .env.example .env"
fi

echo ""
echo "3. Docker Containers Status"
echo "---------------------------"

# Check if containers are running
if docker info &> /dev/null; then
    # Check PostgreSQL container
    if docker ps --format "table {{.Names}}" | grep -q "ai_diary_companion_db"; then
        echo -e "${GREEN}✓${NC} PostgreSQL container: running"

        # Check database health
        if docker exec ai_diary_companion_db pg_isready -U postgres &> /dev/null; then
            echo -e "${GREEN}✓${NC} PostgreSQL: healthy"
        else
            echo -e "${YELLOW}⚠${NC} PostgreSQL: starting up..."
        fi
    else
        echo -e "${BLUE}ℹ${NC} PostgreSQL container: not running"
        echo "  Run: docker compose up -d postgres"
    fi

    # Check app container
    if docker ps --format "table {{.Names}}" | grep -q "ai_diary_companion_app"; then
        echo -e "${GREEN}✓${NC} App container: running"

        # Check API health
        if curl -s http://localhost:8000/health &> /dev/null; then
            echo -e "${GREEN}✓${NC} FastAPI: healthy"
            API_INFO=$(curl -s http://localhost:8000/ 2>/dev/null)
            if [ -n "$API_INFO" ]; then
                MESSAGE=$(echo $API_INFO | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'OK'))" 2>/dev/null || echo "OK")
                echo -e "${GREEN}✓${NC} API response: $MESSAGE"
            fi
        else
            echo -e "${YELLOW}⚠${NC} FastAPI: not responding"
        fi
    else
        echo -e "${BLUE}ℹ${NC} App container: not running"
        echo "  Run: docker compose up -d app"
    fi
fi

echo ""
echo "4. Docker Images"
echo "----------------"

# Check if images exist
if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "llm-chat-sandbox"; then
    echo -e "${GREEN}✓${NC} App image: built"
    IMAGE_SIZE=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep llm-chat-sandbox | awk '{print $3}')
    echo "  Size: $IMAGE_SIZE"
else
    echo -e "${BLUE}ℹ${NC} App image: not built"
    echo "  Run: docker compose build"
fi

if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "postgres:17"; then
    echo -e "${GREEN}✓${NC} PostgreSQL image: downloaded"
else
    echo -e "${BLUE}ℹ${NC} PostgreSQL image: not downloaded"
    echo "  Will be downloaded on first run"
fi

echo ""
echo "5. Quick Start Commands"
echo "-----------------------"
echo -e "${BLUE}Start all services:${NC}"
echo "  docker compose up -d"
echo ""
echo -e "${BLUE}View logs:${NC}"
echo "  docker compose logs -f"
echo ""
echo -e "${BLUE}Run migrations:${NC}"
echo "  docker compose --profile migrate up migrate"
echo ""
echo -e "${BLUE}Stop services:${NC}"
echo "  docker compose down"
echo ""
echo -e "${BLUE}Clean everything:${NC}"
echo "  docker compose down -v"

echo ""
echo "====================================="
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ Docker environment is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env if not done"
    echo "2. Set GROQ_API_KEY in .env file"
    echo "3. Run: docker compose up -d"
    echo "4. Access API at http://localhost:8000"
else
    echo -e "${RED}❌ Some requirements are missing.${NC}"
    echo "Please address the issues above before proceeding."
fi
echo "====================================="