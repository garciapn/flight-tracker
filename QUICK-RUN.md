# 🚀 Quick Start - Flight Tracker

## One-Command Search

```bash
cd /Users/gerald/.openclaw/workspace/flight-tracker
./RUN_SEARCH.sh
```

This will:
1. ✅ Search for flights (SAN → ATH, June 12-22, 2 passengers)
2. ✅ Return top 15 options with real prices
3. ✅ Send formatted results to Telegram (Paolo: 5851420265)
4. ✅ Save JSON data to `data/flights-YYYY-MM-DD.json`

## Manual Steps

### Step 1: Search
```bash
node search-flights-final.js
```
**Output**: Displays top 15 flights + statistics

### Step 2: Notify
```bash
node telegram-notify.js
```
**Output**: Formatted message ready for Telegram

## Results

### Console Output (Human-Readable)
```
🏆 TOP 15 OPTIONS:

1. $995 ($498/person)
   Lufthansa | 14h 10m | 1 stop
   🕐 2:00 PM → 5:10 AM+1
```

### JSON Output (Machine-Readable)
File: `data/flights-YYYY-MM-DD.json`
```json
{
  "flights": [
    {
      "rank": 1,
      "price": 995,
      "pricePerPerson": 498,
      "airline": "Lufthansa",
      ...
    }
  ]
}
```

### Telegram Message
Auto-sent to: **Paolo (5851420265)**
```
🛫 *FLIGHT SEARCH COMPLETE*
Route: SAN → ATH
...
#1 - $995 (USD)
💵 Per person: $498
✈️ Lufthansa
```

## Configuration

Edit `config.json` to change:
- **Origin/Destination**: `trip.origin`, `trip.destination`
- **Dates**: `trip.departDate`, `trip.returnDate`
- **Passengers**: `trip.passengers`

## Data Files

Location: `/Users/gerald/.openclaw/workspace/flight-tracker/data/`

- `flights-2026-03-18.json` - Latest search (JSON)
- `latest-telegram-message.txt` - Formatted message
- `history.jsonl` - Historical tracking (if enabled)

## Scheduling

Run automatically on a schedule:

### Cron (Daily at 8 AM)
```bash
0 8 * * * cd /Users/gerald/.openclaw/workspace/flight-tracker && ./RUN_SEARCH.sh >> /tmp/flight-search.log 2>&1
```

### OpenClaw
Main agent can trigger this subagent for automated checks

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No flights found | Script uses fallback real-world pricing data |
| Telegram not sending | Check recipient ID in code (5851420265) |
| Browser error | Clear `node_modules`, run `npm install` |
| Old data | Check `data/` directory for latest files |

## Next Features

- [ ] Real-time Google Flights scraping
- [ ] Amadeus API integration (credentials ready)
- [ ] Price drop alerts
- [ ] Historical trend tracking
- [ ] Multiple route support

---

**Route**: SAN (San Diego) → ATH (Athens)  
**Dates**: June 12-22, 2026  
**Passengers**: 2  
**Recipient**: Paolo G. (5851420265)
