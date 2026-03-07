# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-07

### Added
- ✨ Initial release of Flight Tracker
- Real-time flight price monitoring via Amadeus API
- 250+ flight combination tracking per collection
- Modern Flask-based dashboard with responsive UI
- Automated data collection with launchd scheduler (2x daily)
- Price alert system (triggers when prices drop below threshold)
- Historical price analysis with trend indicators
- JSONL-based price history for analytics
- Layover and flight duration tracking
- Airline-specific price history

### Features
- **API Integration**: Amadeus Flight Search API with test sandbox
- **Data Pipeline**: Automated collection, validation, and storage
- **Fallback System**: Uses cached API data if Amadeus times out
- **Smart Alerts**: JSON-based alert generation and tracking
- **Analytics**: Price statistics, trends, and historical comparisons
- **Dashboard**: Real-time price display with Chart.js visualizations

### Technical
- Flask 2.3.0 for web server
- Python 3.9+ compatible
- macOS launchd for scheduling
- Pure JSON/JSONL for data persistence
- No database required

## Future Roadmap

### v1.1.0 (Q2 2026)
- [ ] Multi-route support (SFO, LAX, SEA)
- [ ] Email alert notifications
- [ ] Persistent database (SQLite or PostgreSQL)
- [ ] API endpoints for programmatic access

### v1.2.0 (Q3 2026)
- [ ] Price prediction using ML
- [ ] Mobile app (React Native)
- [ ] Google Flights API comparison
- [ ] Integration with booking platforms

### v2.0.0 (2026)
- [ ] Microservices architecture
- [ ] Real-time WebSocket updates
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment
