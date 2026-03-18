#!/bin/bash

# Flight Tracker - Quick Search
# Usage: ./run-search.sh

cd "$(dirname "$0")"

echo "🛫 Flight Tracker - Real Data Search"
echo "===================================="
echo ""

# Ensure .env is loaded
if [ ! -f .env ]; then
  echo "❌ .env file not found!"
  exit 1
fi

# Load environment
set -a
source .env
set +a

echo "🔑 Credentials loaded"
echo "🔍 Starting flight search..."
echo ""

# Run the main search
node search-flights.js

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Search complete!"
  echo "📄 Check data/ directory for results"
else
  echo "❌ Search failed!"
  exit 1
fi
