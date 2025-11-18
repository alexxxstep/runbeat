#!/bin/bash

# Script to test error logging system
# Usage: ./scripts/test_error_logging.sh

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
API_PREFIX="/api/v1"

echo "🧪 Testing Error Logging System"
echo "================================"
echo "Backend URL: $BACKEND_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -w "\n%{http_code}" "$url")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $status_code, expected $expected_status)"
        echo "Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1️⃣  Testing Health Endpoint"
echo "----------------------------"
test_endpoint "Health Check" "$BACKEND_URL/health"
echo ""

echo "2️⃣  Testing Error Logging Endpoints"
echo "------------------------------------"
test_endpoint "Trigger ERROR" "$BACKEND_URL$API_PREFIX/test-error-logging/trigger-error"
sleep 1

test_endpoint "Trigger CRITICAL" "$BACKEND_URL$API_PREFIX/test-error-logging/trigger-critical"
sleep 1

test_endpoint "Trigger WARNING" "$BACKEND_URL$API_PREFIX/test-error-logging/trigger-warning"
sleep 1

test_endpoint "Trigger Exception" "$BACKEND_URL$API_PREFIX/test-error-logging/trigger-exception"
sleep 1

test_endpoint "Direct Log" "$BACKEND_URL$API_PREFIX/test-error-logging/direct-log?message=Test&level=ERROR" 200
sleep 1

echo ""
echo "3️⃣  Checking Recent Logs"
echo "------------------------"
response=$(curl -s "$BACKEND_URL$API_PREFIX/test-error-logging/check-recent-logs?limit=5")
count=$(echo "$response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')

if [ -n "$count" ] && [ "$count" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $count recent logs${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ No logs found in database${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "📊 Test Results"
echo "==============="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

