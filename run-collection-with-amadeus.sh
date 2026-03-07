#!/bin/bash
# Flight Tracker - Data Collection with Amadeus API
# Loads credentials, runs collection, and analyzes results

cd /Users/gerald/.openclaw/workspace/flight-tracker

# Load Amadeus credentials
source .env

# Run collection
python3 collect-data.py
COLLECTION_EXIT=$?

# If collection succeeded, run analysis
if [ $COLLECTION_EXIT -eq 0 ]; then
    python3 analyze-prices.py
else
    echo "Collection failed, skipping analysis"
    exit 1
fi
