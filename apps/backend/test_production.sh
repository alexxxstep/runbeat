#!/bin/bash
# Production testing script for RunBeat Backend
# Usage: ./test_production.sh <your-railway-url>

RAILWAY_URL=${1:-"your-project.railway.app"}

echo "🧪 Testing RunBeat Backend on Railway"
echo "URL: https://${RAILWAY_URL}"
echo ""

echo "1️⃣ Health Check:"
curl -s "https://${RAILWAY_URL}/health" | jq '.' || curl -s "https://${RAILWAY_URL}/health"
echo ""
echo ""

echo "2️⃣ Readiness Check:"
curl -s "https://${RAILWAY_URL}/health/ready" | jq '.' || curl -s "https://${RAILWAY_URL}/health/ready"
echo ""
echo ""

echo "3️⃣ Liveness Check:"
curl -s "https://${RAILWAY_URL}/health/live" | jq '.' || curl -s "https://${RAILWAY_URL}/health/live"
echo ""
echo ""

echo "✅ Testing complete!"

