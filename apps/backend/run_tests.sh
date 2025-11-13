#!/bin/bash

# Run all tests for RunBeat Backend

echo "🧪 Running RunBeat Backend Tests..."
echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run tests
echo "🚀 Running tests..."
python -m pytest tests/ -v --tb=short --color=yes

# Summary
echo ""
echo "✅ Tests completed!"

