# Flight Tracker API

Complete API reference for Flight Tracker endpoints.

## Base URL

```
http://localhost:3737
```

## Authentication

No authentication required. All endpoints are public.

## Endpoints

### Dashboard & UI

#### GET /

Returns the main dashboard HTML page.

**Response:** HTML document

```bash
curl http://localhost:3737/
```

---

### Flights

#### GET /api/flights

Get the latest flight prices with historical analysis.

**Query Parameters:**
- `route` (optional) — Filter by route (e.g., `SAN-ATH`)
- `limit` (optional) — Number of flights (default: 15)

**Response:**
```json
{
  "flights": [
    {
      "airline": "United, Air Canada",
      "price": 1120,
      "price_per_person": "$1,120",
      "price_round_trip": "$2,240",
      "departure": "06:30 AM",
      "arrival": "08:30 PM +1",
      "duration": "15h 00m",
      "stops": "1 stop",
      "layover": "3h 45m in YYC",
      "layover_time": "3h 45m",
      "avg_historical_price": "$1,150",
      "pct_change": "-2.6%",
      "price_color": "green",
      "booking_url": "https://www.google.com/travel/flights?...",
      "amadeus_id": "1",
      "source": "amadeus"
    }
  ],
  "timestamp": "2026-03-07T12:01:18Z",
  "stats": {
    "min_price": 1120,
    "max_price": 1400,
    "avg_price": 1150,
    "total_flights": 28
  }
}
```

**Example:**
```bash
curl http://localhost:3737/api/flights
curl "http://localhost:3737/api/flights?limit=5"
curl "http://localhost:3737/api/flights?route=SAN-ATH"
```

---

#### GET /api/dashboard

Get dashboard data with charts and statistics.

**Response:**
```json
{
  "flights": [...],
  "trends": [
    {
      "date": "2026-03-07",
      "min_price": 1120,
      "max_price": 1400,
      "avg_price": 1150,
      "flight_count": 28
    }
  ],
  "price_history": {
    "dates": ["2026-03-06", "2026-03-07"],
    "prices": [1131, 1150]
  }
}
```

**Example:**
```bash
curl http://localhost:3737/api/dashboard
```

---

### Data Export

#### GET /api/data

Get raw flight data in JSON format.

**Response:**
```json
{
  "timestamp": "2026-03-07T12:01:18Z",
  "flights": [...],
  "stats": {...}
}
```

**Example:**
```bash
curl http://localhost:3737/api/data | jq .
```

Export to file:
```bash
curl http://localhost:3737/api/data > flights.json
```

---

### Flight History

#### GET /api/flight-history/<airline>

Get historical price data for a specific airline.

**Path Parameters:**
- `airline` — Airline name (URL-encoded, e.g., "United%2C%20Air%20Canada")

**Response:**
```json
{
  "airline": "United, Air Canada",
  "history": [
    {
      "date": "2026-03-06",
      "price": 1131
    },
    {
      "date": "2026-03-07",
      "price": 1120
    }
  ],
  "stats": {
    "min": 1120,
    "max": 1131,
    "avg": 1125.5,
    "trend": "down"
  }
}
```

**Example:**
```bash
# URL encode the airline name
curl "http://localhost:3737/api/flight-history/United%2C%20Air%20Canada"
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Not found |
| 500 | Server error |

## Data Formats

### Flight Object

```json
{
  "airline": "string",              // e.g., "United, Air Canada"
  "price": 1120,                    // Per-person price in USD (integer)
  "price_per_person": "$1,120",    // Formatted per-person price
  "price_round_trip": "$2,240",    // Formatted round-trip price
  "departure": "string",            // e.g., "06:30 AM"
  "arrival": "string",              // e.g., "08:30 PM +1"
  "duration": "string",             // e.g., "15h 00m"
  "stops": "string",                // e.g., "1 stop" or "nonstop"
  "layover": "string",              // e.g., "3h 45m in YYC"
  "layover_time": "string",         // e.g., "3h 45m"
  "booking_url": "string",          // Direct booking link
  "amadeus_id": "string",           // Flight identifier
  "source": "string",               // "amadeus" or "flask_api"
  "avg_historical_price": "$1,150", // Historical average
  "pct_change": "-2.6%",            // Price change vs average
  "price_color": "green"            // "green" (down), "red" (up), "gray" (unknown)
}
```

### Stats Object

```json
{
  "min_price": 1120,        // Lowest price found
  "max_price": 1400,        // Highest price found
  "avg_price": 1150,        // Average price
  "total_flights": 28       // Total flight options tracked
}
```

## Rate Limiting

No rate limiting. Feel free to make as many requests as you want!

## CORS

CORS is not enabled by default. If you need cross-origin requests, modify `app.py`:

```python
from flask_cors import CORS
CORS(app)
```

Then install: `pip install flask-cors`

## Error Handling

On error, the API returns:

```json
{
  "error": "Description of what went wrong",
  "status": 500
}
```

## Examples

### Get 5 cheapest flights
```bash
curl "http://localhost:3737/api/flights?limit=5" | jq .flights
```

### Get price history for a carrier
```bash
curl "http://localhost:3737/api/flight-history/United%2C%20Air%20Canada" | jq .history
```

### Export all data
```bash
curl http://localhost:3737/api/data > data-export-$(date +%Y-%m-%d).json
```

### Monitor prices in real-time
```bash
watch -n 300 "curl -s http://localhost:3737/api/flights | jq '.stats'"
```

## Webhooks

Not currently supported, but planned for v1.2.0!

## Changelog

### v1.0.0 (2026-03-07)
- Initial API release
- All endpoints functional
- Real-time Amadeus API integration
