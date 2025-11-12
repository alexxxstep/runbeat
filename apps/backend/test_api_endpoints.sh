#!/bin/bash
# Simple HTTP tests for new API endpoints
# Run this after starting the server: uvicorn app.main:app --reload

BASE_URL="${1:-http://localhost:8000}"

echo "Testing RunBeat API endpoints at $BASE_URL"
echo "=========================================="
echo ""

# Test 1: Spotify Auth Initiate
echo "1. Testing GET /auth/spotify"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/auth/spotify")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo "   ✅ Status: $http_code"
    echo "   Response: $body" | head -c 100
    echo ""
else
    echo "   ❌ Status: $http_code"
fi
echo ""

# Test 2: Get Workouts (will fail without auth, but checks endpoint exists)
echo "2. Testing GET /workouts"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/workouts?user_id=test")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 422 ] || [ "$http_code" -eq 500 ]; then
    echo "   ✅ Endpoint exists (Status: $http_code)"
else
    echo "   ❌ Status: $http_code"
fi
echo ""

# Test 3: Get User Preferences
echo "3. Testing GET /users/{user_id}/preferences"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/users/test/preferences")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 404 ] || [ "$http_code" -eq 500 ]; then
    echo "   ✅ Endpoint exists (Status: $http_code)"
else
    echo "   ❌ Status: $http_code"
fi
echo ""

# Test 4: Get Playlist History
echo "4. Testing GET /playlists/history"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/playlists/history?user_id=test")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 422 ] || [ "$http_code" -eq 500 ]; then
    echo "   ✅ Endpoint exists (Status: $http_code)"
else
    echo "   ❌ Status: $http_code"
fi
echo ""

# Test 5: Health check (should always work)
echo "5. Testing GET /health"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ]; then
    echo "   ✅ Status: $http_code"
else
    echo "   ❌ Status: $http_code"
fi
echo ""

echo "=========================================="
echo "Tests completed!"
echo ""
echo "Note: Some endpoints may return errors without proper authentication or database setup."
echo "This script only verifies that endpoints are accessible."

