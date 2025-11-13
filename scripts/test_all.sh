#!/bin/bash

# Comprehensive Testing Script for RunBeat
# This script tests all major components of the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-https://runbeatbackend-production.up.railway.app}"
FRONTEND_URL="${FRONTEND_URL:-https://runbeatweb-production.up.railway.app}"

echo -e "${GREEN}=== RunBeat Comprehensive Testing ===${NC}\n"

# Test counter
PASSED=0
FAILED=0
TOTAL=0

# Function to run a test
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"

    TOTAL=$((TOTAL + 1))

    echo -n "Testing $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL$endpoint" || echo -e "\n000")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint" || echo -e "\n000")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint" || echo -e "\n000")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE \
            "$BACKEND_URL$endpoint" || echo -e "\n000")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_status)"
        echo -e "${YELLOW}Response: $body${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Health Check Tests
echo -e "\n${GREEN}1. Health Check Tests${NC}"
echo "========================"

test_endpoint "Health Check" "GET" "/health" "" 200
test_endpoint "Readiness Check" "GET" "/health/ready" "" 200

# 2. Authentication Tests (Note: These require manual OAuth flow)
echo -e "\n${GREEN}2. Authentication Tests${NC}"
echo "=========================="
echo -e "${YELLOW}Note: OAuth tests require manual interaction${NC}"

# 3. Chat Tests (Note: Requires user_id and OpenAI)
echo -e "\n${GREEN}3. Chat Tests${NC}"
echo "=============="
echo -e "${YELLOW}Note: Chat tests require user_id and OpenAI API key${NC}"

# 4. Workouts Tests (Note: Requires user_id)
echo -e "\n${GREEN}4. Workouts Tests${NC}"
echo "=================="
echo -e "${YELLOW}Note: Workout tests require user_id${NC}"

# 5. Playlists Tests (Note: Requires user_id and Spotify auth)
echo -e "\n${GREEN}5. Playlists Tests${NC}"
echo "==================="
echo -e "${YELLOW}Note: Playlist tests require user_id and Spotify authentication${NC}"

# Summary
echo -e "\n${GREEN}=== Test Summary ===${NC}"
echo "Total tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All automated tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi

