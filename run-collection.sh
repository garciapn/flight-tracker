#!/bin/bash
# Flight Tracker - Data Collection Cron Job
# Runs 2x daily (8 AM & 8 PM PST)
# Collects flight data and saves to local JSON files

set -e

BASE_DIR="/Users/gerald/.openclaw/workspace/flight-tracker"
DATA_DIR="$BASE_DIR/data"
LOG_DIR="$BASE_DIR/logs"
PYTHON="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"

# Create directories
mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

# Timestamp for logging
TS=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$LOG_DIR/collection_$(date '+%Y%m%d').log"

echo "[$TS] Starting flight data collection..." >> "$LOG_FILE"

# Run the collection script with the correct Python version
cd "$BASE_DIR"
$PYTHON collect-data.py >> "$LOG_FILE" 2>&1 || {
    echo "[$TS] ERROR: Collection script failed" >> "$LOG_FILE"
    exit 1
}

echo "[$TS] Collection complete" >> "$LOG_FILE"
