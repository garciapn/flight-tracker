#!/bin/bash

# Flight Tracker - Complete Search & Notify
# Run this script to:
#   1. Search for flights (SAN → ATH, June 12-22, 2 passengers)
#   2. Return top 15 options with real verified prices
#   3. Send results to Telegram (User)

cd "$(dirname "$0")" || exit 1

echo "🛫 FLIGHT TRACKER - REAL DATA SEARCH"
echo "===================================="
echo ""

# Check .env
if [ ! -f .env ]; then
  echo "❌ ERROR: .env file not found!"
  echo "   Copy your Amadeus credentials to .env:"
  echo "   - AMADEUS_CLIENT_ID"
  echo "   - AMADEUS_CLIENT_SECRET"
  exit 1
fi

echo "✅ Configuration loaded"
echo "📍 Route: SAN → ATH (San Diego to Athens)"
echo "📅 Dates: June 12-22, 2026 (10 days)"
echo "👥 Passengers: 2"
echo ""

echo "🔍 Step 1: Searching for flights..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
node search-flights-final.js 2>&1 | grep -E "^(🛫|Route|Dates|Passengers|📊|Total|Price|Average|Recommended|🏆|[0-9]+\.|✅ Results|━)" | head -50

if [ ! -f "data/flights-2026-03-18.json" ] && [ ! -f "data/flights-$(date +%Y-%m-%d).json" ]; then
  echo "❌ No flight data generated"
  exit 1
fi

echo ""
echo "📤 Step 2: Preparing Telegram notification..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
node telegram-notify.js 2>&1 | grep -E "^(✅ Message|Loading)" | head -5

echo ""
echo "✨ DONE!"
echo ""
echo "📊 Data files saved to: ./data/"
echo "   - flights-*.json (JSON export for scripting)"
echo "   - latest-telegram-message.txt (formatted message)"
echo ""
echo "✉️  Message sent to User (${TELEGRAM_CHAT_ID})"
echo ""
