# ✈️ Flight Tracker

Real-time flight price tracker for San Diego (SAN) ↔ Athens (ATH) using the **Amadeus API**. Built with Python, Flask, and automated data collection.

## Features

✨ **Live Price Tracking**
- Real-time flight prices via Amadeus API
- 250+ flight combinations analyzed per run
- Historical price trends and analysis

📊 **Dashboard**
- Modern, responsive web UI
- Price alerts when deals drop below threshold
- Airline-specific price history
- Trend indicators (📈 📉)

⚙️ **Automated Collection**
- Scheduled cron jobs (8 AM & 8 PM PST)
- Smart fallback to cached API if Amadeus times out
- Data validation (price sanity checks, structure validation)
- Automatic alert generation

💾 **Data Pipeline**
- JSON-based storage (daily snapshots + history)
- JSONL history file for trend analysis
- Price statistics (min, max, average, % change)

## Stack

- **Backend**: Flask (Python 3.9+)
- **API**: Amadeus Flight Search API
- **Frontend**: HTML5 + CSS3 + Chart.js
- **Scheduling**: macOS launchd
- **Storage**: JSON + JSONL files

## Setup

### Requirements
- Python 3.9+
- Amadeus API credentials (free sandbox available)
- macOS (for launchd) or equivalent scheduler

### Installation

```bash
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask

# Set up environment
cp .env.example .env
# Add your Amadeus credentials:
# AMADEUS_CLIENT_ID=your_id
# AMADEUS_CLIENT_SECRET=your_secret
```

### Running Locally

```bash
# Start the Flask server
python3 app.py
# Visit http://localhost:3737
```

### Automated Collection

Set up launchd for scheduled collection:

```bash
# Copy the plist to launchd
cp com.flighttracker.collect.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.flighttracker.collect.plist

# Manually trigger collection
bash run-collection-with-amadeus.sh
```

## Project Structure

```
flight-tracker/
├── app.py                          # Flask server
├── collect-data.py                 # Data collection script
├── analyze-prices.py               # Price analysis & insights
├── amadeus-scraper.py              # Amadeus API wrapper
├── run-collection-with-amadeus.sh  # Cron job runner
├── data/                           # Flight data (git-ignored)
│   ├── 2026-03-07.json            # Daily snapshot
│   ├── history.jsonl              # Price history
│   └── screenshots/               # Dashboard captures
├── alerts/                         # Price alerts (git-ignored)
└── templates/                      # HTML templates
```

## Data Format

**Daily Flight Data** (`data/YYYY-MM-DD.json`):
```json
{
  "timestamp": "2026-03-07T12:01:18Z",
  "flights": [
    {
      "airline": "United, Air Canada",
      "price": 1120,
      "departure": "06:30 AM",
      "arrival": "08:30 PM",
      "duration": "15h 00m",
      "stops": "1 stop",
      "layover": "3h 45m in YYC"
    }
  ]
}
```

**Price Alerts** (`alerts/alert_*.json`):
```json
{
  "airline": "United, Air Canada",
  "price": 1120,
  "threshold": 1200,
  "status": "triggered"
}
```

## Key Metrics

- **Current Best Price**: $1,120/person (March 7, 2026)
- **Price Range**: $1,120 - $1,400/person
- **Average**: $1,131/person
- **Trend**: 📉 Dropping (good news!)
- **Data Points**: 28 flights per collection
- **Collection Frequency**: 2x daily

## Development

### Adding Features

1. **New Routes**: Add to `app.py`
2. **Price Analysis**: Enhance `analyze-prices.py`
3. **Data Collection**: Modify `collect-data.py`
4. **UI**: Update HTML in `templates/`

### Testing

```bash
# Manual data collection
python3 collect-data.py

# Analyze prices
python3 analyze-prices.py

# Check API
curl http://localhost:3737/api/flights
```

## API Endpoints

- `GET /` - Dashboard UI
- `GET /api/flights` - Top 15 flights with history
- `GET /api/flights?route=SAN-ATH` - Filter by route
- `GET /api/dashboard` - Dashboard data
- `GET /api/data` - Raw data export
- `GET /api/flight-history/<airline>` - Airline price history

## Future Ideas

- [ ] Multi-route support (SFO, LAX, etc.)
- [ ] Mobile app
- [ ] Email alerts
- [ ] Price prediction ML model
- [ ] Comparison with Google Flights API
- [ ] Integration with booking platforms

## License

MIT

## Author

**Paolo Garcia**  
Travel optimizer & flight deal hunter 🧳✈️

---

*Saving money on flights, one API call at a time.*
