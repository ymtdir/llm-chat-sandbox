#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "====================================="
echo "AI Diary Companion - Setup Verification"
echo "====================================="
echo ""

# Track overall status
ALL_PASSED=true

# Function to check command exists
check_command() {
    local cmd=$1
    local display_name=$2
    local min_version=$3
    local get_version_cmd=$4

    if command -v $cmd &> /dev/null; then
        if [ -n "$get_version_cmd" ]; then
            version=$(eval $get_version_cmd)
            echo -e "${GREEN}✓${NC} $display_name: $version"
        else
            echo -e "${GREEN}✓${NC} $display_name: installed"
        fi
    else
        echo -e "${RED}✗${NC} $display_name: not found"
        ALL_PASSED=false
        return 1
    fi

    if [ -n "$min_version" ]; then
        # Version check logic here if needed
        :
    fi

    return 0
}

echo "1. System Requirements"
echo "----------------------"

# Check Python 3.12
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
    echo -e "${GREEN}✓${NC} Python version file: $PYTHON_VERSION"

    if command -v python &> /dev/null; then
        ACTUAL_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        if [[ $ACTUAL_VERSION == 3.12.* ]]; then
            echo -e "${GREEN}✓${NC} Python 3.12: $ACTUAL_VERSION"
        else
            echo -e "${RED}✗${NC} Python 3.12 required, found: $ACTUAL_VERSION"
            ALL_PASSED=false
        fi
    else
        echo -e "${RED}✗${NC} Python not found in PATH"
        ALL_PASSED=false
    fi
else
    echo -e "${YELLOW}⚠${NC} .python-version file not found"
fi

# Check Node.js
check_command "node" "Node.js" "22.0.0" "node --version"

# Check PostgreSQL
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    if [[ $PSQL_VERSION == 17.* ]]; then
        echo -e "${GREEN}✓${NC} PostgreSQL 17.x: $PSQL_VERSION"
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL found but not version 17: $PSQL_VERSION"
    fi
else
    echo -e "${RED}✗${NC} PostgreSQL 17.x: not installed"
    ALL_PASSED=false
fi

echo ""
echo "2. Environment Configuration"
echo "----------------------------"

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check critical environment variables
    source .env 2>/dev/null

    if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" != "your-secret-key-here-change-in-production" ]; then
        echo -e "${GREEN}✓${NC} JWT Secret Key: configured"
    else
        echo -e "${YELLOW}⚠${NC} JWT Secret Key: using default (change for production)"
    fi

    if [ -n "$DATABASE_URL" ]; then
        echo -e "${GREEN}✓${NC} Database URL: configured"
    else
        echo -e "${RED}✗${NC} Database URL: not configured"
        ALL_PASSED=false
    fi

    if [ -n "$GROQ_API_KEY" ] && [ "$GROQ_API_KEY" != "your-groq-api-key-here" ]; then
        echo -e "${GREEN}✓${NC} Groq API Key: configured"
    else
        echo -e "${YELLOW}⚠${NC} Groq API Key: not configured (required for LLM features)"
    fi
else
    echo -e "${RED}✗${NC} .env file not found (copy from .env.example)"
    ALL_PASSED=false
fi

echo ""
echo "3. Python Dependencies"
echo "----------------------"

# Check virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment: exists"

    # Activate venv and check packages
    source venv/bin/activate 2>/dev/null

    # Check critical packages
    PACKAGES=("fastapi" "sqlalchemy" "alembic" "groq" "firebase-admin" "uvicorn")
    for pkg in "${PACKAGES[@]}"; do
        if pip show $pkg &> /dev/null; then
            version=$(pip show $pkg | grep Version | cut -d' ' -f2)
            echo -e "${GREEN}✓${NC} $pkg: $version"
        else
            echo -e "${RED}✗${NC} $pkg: not installed"
            ALL_PASSED=false
        fi
    done
else
    echo -e "${RED}✗${NC} Virtual environment not found"
    echo "  Run: python -m venv venv"
    ALL_PASSED=false
fi

echo ""
echo "4. Database Status"
echo "------------------"

# Check if databases exist
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
if command -v psql &> /dev/null; then
    # Check main database
    if psql -lqt | cut -d \| -f 1 | grep -qw ai_diary_companion; then
        echo -e "${GREEN}✓${NC} Main database: ai_diary_companion exists"
    else
        echo -e "${RED}✗${NC} Main database: ai_diary_companion not found"
        echo "  Run: createdb ai_diary_companion"
        ALL_PASSED=false
    fi

    # Check test database
    if psql -lqt | cut -d \| -f 1 | grep -qw ai_diary_companion_test; then
        echo -e "${GREEN}✓${NC} Test database: ai_diary_companion_test exists"
    else
        echo -e "${YELLOW}⚠${NC} Test database: ai_diary_companion_test not found"
        echo "  Run: createdb ai_diary_companion_test"
    fi
fi

echo ""
echo "5. Application Status"
echo "--------------------"

# Check if API is running
if curl -s http://127.0.0.1:8000/health &> /dev/null; then
    echo -e "${GREEN}✓${NC} FastAPI server: running on http://127.0.0.1:8000"

    # Get API info
    API_INFO=$(curl -s http://127.0.0.1:8000/)
    if [ -n "$API_INFO" ]; then
        echo -e "${GREEN}✓${NC} API responds: $(echo $API_INFO | jq -r '.message' 2>/dev/null || echo 'OK')"
    fi
else
    echo -e "${YELLOW}⚠${NC} FastAPI server: not running"
    echo "  Run: source venv/bin/activate && uvicorn app.main:app --reload"
fi

echo ""
echo "====================================="
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All critical requirements satisfied!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure Groq API key in .env file"
    echo "2. Set up Firebase credentials for push notifications"
    echo "3. Run database migrations: alembic upgrade head"
    echo "4. Start development: uvicorn app.main:app --reload"
else
    echo -e "${RED}❌ Some requirements are missing.${NC}"
    echo "Please address the issues above before proceeding."
fi
echo "====================================="