#!/bin/bash

# Test logout endpoint
# Usage: ./test_logout_endpoint.sh [user_id]

set -e

API_URL="${API_URL:-http://localhost:8000}"
USER_ID="${1:-test-user-id}"

echo "🧪 Testing Logout Endpoint"
echo "=========================="
echo "API URL: $API_URL"
echo "User ID: $USER_ID"
echo ""

# Test 1: Logout with valid user
echo "📝 Test 1: Logout with valid user"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/logout?user_id=$USER_ID")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✅ Success: $body"
else
    echo "❌ Failed with status $http_code: $body"
fi
echo ""

# Test 2: Logout with non-existent user
echo "📝 Test 2: Logout with non-existent user"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/logout?user_id=nonexistent-user-id")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "404" ]; then
    echo "✅ Success (expected 404): $body"
else
    echo "❌ Failed with status $http_code: $body"
fi
echo ""

# Test 3: Logout without user_id
echo "📝 Test 3: Logout without user_id parameter"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/logout")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "422" ]; then
    echo "✅ Success (expected 422): $body"
else
    echo "❌ Failed with status $http_code: $body"
fi
echo ""

echo "=========================="
echo "✅ All tests completed!"

