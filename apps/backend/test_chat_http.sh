#!/bin/bash
# Test chat endpoint via HTTP
# Usage: ./test_chat_http.sh [url]

BASE_URL=${1:-"http://localhost:8000"}

echo "=========================================="
echo "Testing Chat Endpoint via HTTP"
echo "URL: $BASE_URL"
echo "=========================================="

echo ""
echo "Test 1: Simple workout"
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Легке відновлення 30 хвилин"}' \
  | python -m json.tool

echo ""
echo ""
echo "Test 2: Workout requiring clarification"
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Хочу пробігти 40 хв з інтервалами"}' \
  | python -m json.tool

echo ""
echo ""
echo "Test 3: Progressive workout"
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Прогресивний біг 45 хвилин від легкого до швидкого"}' \
  | python -m json.tool

echo ""
echo "=========================================="
echo "Testing complete!"
echo "=========================================="

