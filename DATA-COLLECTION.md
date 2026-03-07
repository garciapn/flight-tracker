# Flight Tracker - Data Collection (File-Based)

## Overview

Flight data is collected **2x daily** (8 AM & 8 PM PST) via cron jobs and saved to local JSON files.

## Files

### Daily Files
- **Location:** `data/YYYY-MM-DD.json`
- **Content:** Flight options for that day + metadata
- **Timestamp:** UTC (add 8 hours for PST)
- **Flights:** 5 options, sorted by price (lowest first)

```json
{
  "timestamp": "2026-02-25T21:33:27.763002",
  "route": "SAN→ATH",
  "trip_date": "2026-06-12",
  "return_date": "2026-06-22",
  "passengers": 2,
  "flights": [
    {
      "airline": "Airline Name",
      "departure": "10:10 PM",
      "arrival": "7:50 AM+2",
      "duration": "23 hr 40 min",
      "layover": "8 hr 17 min in JFK",
      "price": "$2,532",
      "stops": "1 stop"
    }
  ]
}
```

### History File
- **Location:** `data/history.jsonl`
- **Format:** One JSON object per line (JSONL)
- **Purpose:** Long-term tracking, append-only
- **Size:** Grows with each collection run

```
{"timestamp": "2026-02-25T21:33:27.763002", "route": "SAN→ATH", ...}
{"timestamp": "2026-02-25T13:45:12.654321", "route": "SAN→ATH", ...}
```

### Alert Files
- **Location:** `alerts/alert_TIMESTAMP.json`
- **Created:** When price drops below threshold ($1,200)
- **Contains:** Airline, price, threshold, trigger time

## Cron Jobs

### Morning Collection (8:00 AM PST)
```
0 8 * * * /Users/gerald/.openclaw/workspace/flight-tracker/run-collection.sh
```

### Evening Collection (8:00 PM PST)
```
0 20 * * * /Users/gerald/.openclaw/workspace/flight-tracker/run-collection.sh
```

### Status
View cron jobs:
```bash
openclaw cron list | grep "Flight Tracker"
```

## Scripts

### collect-data.py
Main data collection script:
1. Fetches latest flights from Flask API (`http://localhost:3737/api/flights`)
2. Saves to daily file: `data/YYYY-MM-DD.json`
3. Appends to history: `data/history.jsonl`
4. Checks price alerts
5. Logs to: `logs/collection_YYYYMMDD.log`

**Usage:**
```bash
python3 collect-data.py
```

### run-collection.sh
Wrapper script for cron (loads Python environment):
```bash
./run-collection.sh
```

## Database (Local Files)

No SQL database needed. Everything is in JSON:
- **Query today's flights:** `cat data/2026-02-25.json`
- **View all history:** `cat data/history.jsonl | python3 -m json.tool`
- **Find cheapest:** `jq '.flights[0]' data/2026-02-25.json`
- **Count entries:** `wc -l data/history.jsonl`

## Configuration

Edit `config.json`:
```json
{
  "price_alert_threshold": 1200,
  "trip": {
    "origin": "SAN",
    "destination": "ATH",
    "date": "2026-06-12",
    "return_date": "2026-06-22",
    "passengers": 2
  }
}
```

## Dashboard

The Flask app (`app.py`) reads from these JSON files and displays on `http://localhost:3737`

**Features:**
- Live flight prices
- 7-day price trends
- Price alerts when threshold hit
- Amex points analysis

## Troubleshooting

### No data being collected?
1. Check Flask is running: `curl http://localhost:3737/api/flights`
2. Check cron logs: `cat logs/collection_*.log`
3. Test manually: `python3 collect-data.py`

### Files not updating?
1. Verify cron jobs exist: `openclaw cron list`
2. Check `data/` directory: `ls -la data/`
3. See recent entries: `tail -10 data/history.jsonl`

### API returning 500?
1. Restart Flask: `pkill -f app.py && python3 app.py`
2. Check Flask logs: `python3 app.py` in terminal

## Next Steps

- Set up alerts to send to Telegram when price drops
- Add trend analysis to the dashboard
- Export data to CSV for analysis
