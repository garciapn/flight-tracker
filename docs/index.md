# ✈️ Flight Tracker Documentation

Welcome to the Flight Tracker documentation! Everything you need to get started, deploy, and contribute.

## Quick Links

### Getting Started
- **[Installation](INSTALLATION.md)** — Set up in 5 minutes
- **[Usage Guide](USAGE.md)** — Learn the dashboard
- **[API Reference](API.md)** — Integrate with your apps

### Deploying
- **[Deployment Guide](DEPLOYMENT.md)** — Deploy to production (Heroku, AWS, DigitalOcean, etc.)
- **[Docker Setup](DEPLOYMENT.md#docker-deployment)** — Containerize your app
- **[Scaling](DEPLOYMENT.md#scaling-checklist)** — Handle growth

### Contributing
- **[Contributing Guide](../CONTRIBUTING.md)** — Help us improve
- **[Development](DEVELOPMENT.md)** — Build new features
- **[Running Tests](DEVELOPMENT.md#testing)** — Ensure quality

### Troubleshooting
- **[Installation Guide - Troubleshooting](INSTALLATION.md#troubleshooting)** — Fix setup issues
- **[GitHub Issues](https://github.com/garciapn/flight-tracker/issues)** — Report bugs

---

## What is Flight Tracker?

Flight Tracker is a real-time flight price monitoring system for San Diego (SAN) ↔ Athens (ATH). It uses the Amadeus API to track 250+ flight combinations and alerts you when prices drop below your threshold.

### Features

✨ **Real-time Price Tracking**
- Live flight prices via Amadeus API
- 250+ flight combinations per collection
- Historical price trends

📊 **Dashboard**
- Modern, responsive web interface
- Price alerts & notifications
- Airline-specific history
- Trend indicators

⚙️ **Automated Collection**
- Scheduled data collection (2x daily)
- Smart fallback system
- Data validation
- Automatic alerts

💾 **Data Pipeline**
- JSON-based storage
- JSONL history for analytics
- Price statistics & trends

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Amadeus API credentials
```

### 3. Run

```bash
python3 app.py
# Visit http://localhost:3737
```

### 4. Deploy

See [Deployment Guide](DEPLOYMENT.md) for cloud options.

---

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3.9+) |
| API | Amadeus Flight Search |
| Frontend | HTML5 + CSS3 + Chart.js |
| Scheduling | macOS launchd / cron |
| Storage | JSON + JSONL |
| Testing | pytest |
| Deployment | Docker, Heroku, AWS, etc. |

---

## Project Structure

```
flight-tracker/
├── app.py                       # Flask application
├── collect-data.py              # Data collection
├── analyze-prices.py            # Price analysis
├── email_alerts.py              # Email notifications
├── test_tracker.py              # Unit tests
├── requirements.txt             # Python dependencies
├── docs/                        # Documentation
│   ├── INSTALLATION.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USAGE.md
├── templates/                   # HTML templates
├── data/                        # Flight data (git-ignored)
├── alerts/                      # Price alerts (git-ignored)
└── .github/
    └── workflows/
        └── test.yml             # GitHub Actions CI/CD
```

---

## Key Metrics (as of March 7, 2026)

- **Cheapest Flight**: $1,120/person
- **Average Price**: $1,131/person
- **Price Trend**: 📉 Dropping
- **Data Points**: 28 flights tracked
- **Update Frequency**: 2x daily (8 AM & 8 PM PST)

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Dashboard UI |
| `GET /api/flights` | Current flights |
| `GET /api/dashboard` | Dashboard data |
| `GET /api/data` | Raw export |
| `GET /api/flight-history/<airline>` | Price history |

See [API Reference](API.md) for full documentation.

---

## Email Alerts

Get notified when prices drop:

1. Add email config to `.env`
2. Set `PRICE_THRESHOLD`
3. Alerts send automatically

Example email:
- Subject: "✈️ Flight Deal Alert: $1,120/person (Below $1,200!)"
- Price, flight details, booking link

---

## Contributing

We love contributions! See [Contributing Guide](../CONTRIBUTING.md).

### Ideas for Contributions

- 🌍 Multi-route support (SFO, LAX, etc.)
- 🤖 Price prediction ML model
- 📱 Mobile app (React Native)
- 📧 SMS/Slack alerts
- 💾 Database integration
- 🔍 Advanced search filters

---

## FAQ

**Q: Is this free?**
A: Yes! Flight Tracker is MIT licensed and free to use.

**Q: Do I need API credentials?**
A: Yes, you need a free Amadeus API account (takes 2 minutes).

**Q: Can I track other routes?**
A: Currently hardcoded for SAN→ATH. Multi-route support coming in v1.1!

**Q: How accurate are prices?**
A: Prices come directly from Amadeus. Real-time, very accurate.

**Q: Can I deploy to [platform]?**
A: Probably! See [Deployment Guide](DEPLOYMENT.md) for options.

**Q: How often is data collected?**
A: By default, 2x daily (8 AM & 8 PM PST). You can customize.

**Q: Can I export the data?**
A: Yes! Use `/api/data` endpoint or access JSON files directly.

---

## Support

- 📖 [Read the docs](.)
- 🐛 [Report a bug](https://github.com/garciapn/flight-tracker/issues)
- 💬 [Start a discussion](https://github.com/garciapn/flight-tracker/discussions)
- ⭐ [Star the repo](https://github.com/garciapn/flight-tracker) (means a lot!)

---

## License

MIT License — see [LICENSE](../LICENSE) for details.

## Author

**User Garcia**  
Travel optimizer & flight deal hunter 🧳✈️

---

*Last updated: March 7, 2026*
