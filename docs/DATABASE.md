# Database Setup Guide

Flight Tracker supports both **SQLite** (development) and **PostgreSQL** (production).

## Quick Start

### SQLite (Development - Default)

SQLite is the default. No setup needed!

```bash
python3 app.py
# Database file: ~/.flighttracker/data.db
```

Perfect for:
- Local development
- Testing
- Single-user deployment

### PostgreSQL (Production)

PostgreSQL is recommended for:
- Multiple users
- High-frequency data collection
- Backup & recovery
- Scalability

## SQLite Setup

### Minimal Setup

No installation needed! SQLite comes with Python.

```bash
# Just run the app
python3 app.py
```

Database location: `~/.flighttracker/data.db`

### Backup SQLite Database

```bash
cp ~/.flighttracker/data.db ~/.flighttracker/data.db.backup
```

### Export SQLite to CSV

```bash
sqlite3 ~/.flighttracker/data.db << EOF
.headers on
.mode csv
.output flights.csv
SELECT * FROM flights;
.quit
EOF
```

---

## PostgreSQL Setup

### Installation

#### macOS (Homebrew)

```bash
brew install postgresql@15
brew services start postgresql@15
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Windows

Download [PostgreSQL Installer](https://www.postgresql.org/download/windows/)

#### Docker

```bash
docker run --name flight-tracker-db \
  -e POSTGRES_DB=flight_tracker \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15
```

### Creating Database & User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE flight_tracker;

# Create user
CREATE USER flight_user WITH PASSWORD 'secure_password';

# Grant privileges
ALTER ROLE flight_user SET client_encoding TO 'utf8';
ALTER ROLE flight_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flight_user SET default_transaction_deferrable TO on;
ALTER ROLE flight_user SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE flight_tracker TO flight_user;

# Exit
\q
```

### Configure Flight Tracker

Edit `.env`:

```env
DATABASE_ENV=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=flight_user
DB_PASSWORD=secure_password
DB_NAME=flight_tracker
```

### Initialize Tables

```bash
python3 app.py
# Tables auto-created on first run
```

---

## Migration: SQLite → PostgreSQL

### Step 1: Set Up PostgreSQL

Follow [PostgreSQL Setup](#postgresql-setup) above.

### Step 2: Export SQLite Data

```bash
python3 << 'EOF'
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect(os.path.expanduser('~/.flighttracker/data.db'))
cursor = conn.cursor()

# Export all data
cursor.execute("SELECT * FROM flights")
flights = cursor.fetchall()

with open('flights_backup.json', 'w') as f:
    json.dump([dict(row) for row in flights], f)

conn.close()
print("✅ Data exported to flights_backup.json")
EOF
```

### Step 3: Switch to PostgreSQL

Update `.env`:
```env
DATABASE_ENV=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=flight_user
DB_PASSWORD=secure_password
DB_NAME=flight_tracker
```

### Step 4: Import Data

```bash
python3 << 'EOF'
import json
from models import db, Flight, Collection
from app import app

with app.app_context():
    db.create_all()
    
    with open('flights_backup.json', 'r') as f:
        data = json.load(f)
        for item in data:
            flight = Flight(**item)
            db.session.add(flight)
    
    db.session.commit()
    print("✅ Data imported to PostgreSQL")
EOF
```

### Step 5: Verify

```bash
# Check PostgreSQL
psql -U flight_user -d flight_tracker -c "SELECT COUNT(*) FROM flights;"

# Run app to verify
python3 app.py
```

---

## Database Schema

### flights
- id (PK)
- airline
- price (cents)
- departure
- arrival
- duration
- stops
- layover
- amadeus_id (unique)
- booking_url
- collection_id (FK)
- created_at
- updated_at

### collections
- id (PK)
- timestamp (unique)
- total_flights
- min_price
- max_price
- avg_price
- source

### alerts
- id (PK)
- airline
- price (cents)
- threshold (cents)
- status
- email_sent
- sms_sent
- slack_sent
- discord_sent
- collection_id (FK)
- created_at
- sent_at

### users
- id (PK)
- email (unique)
- phone
- slack_webhook
- discord_webhook
- notify_email
- notify_sms
- notify_slack
- notify_discord
- price_threshold
- created_at
- updated_at

### price_history
- id (PK)
- airline
- price (cents)
- date
- day_of_week
- days_until_flight
- recorded_at

---

## Backup & Recovery

### PostgreSQL Backup

```bash
# Full backup
pg_dump -U flight_user flight_tracker > backup.sql

# Compressed backup
pg_dump -U flight_user flight_tracker | gzip > backup.sql.gz

# Restore
psql -U flight_user flight_tracker < backup.sql
```

### Scheduled Backups

#### Linux/macOS (cron)

```bash
# Daily backup at 2 AM
0 2 * * * pg_dump -U flight_user flight_tracker | gzip > /backups/flight_tracker_$(date +\%Y-\%m-\%d).sql.gz
```

#### GitHub Actions

```yaml
name: Daily Database Backup

on:
  schedule:
    - cron: '0 2 * * *'

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Backup Database
        env:
          DB_URL: ${{ secrets.DATABASE_URL }}
        run: |
          pg_dump $DB_URL | gzip > backup.sql.gz
```

---

## Queries

### Get Latest Prices

```sql
SELECT airline, price, created_at 
FROM flights 
WHERE created_at = (SELECT MAX(created_at) FROM flights)
ORDER BY price;
```

### Price Trends by Airline

```sql
SELECT airline, 
       DATE(created_at) as date,
       MIN(price) as min_price,
       MAX(price) as max_price,
       AVG(price) as avg_price
FROM flights
GROUP BY airline, DATE(created_at)
ORDER BY date DESC;
```

### Alerts Sent

```sql
SELECT airline, price, threshold, 
       email_sent, sms_sent, slack_sent, discord_sent,
       created_at
FROM alerts
WHERE status = 'triggered'
ORDER BY created_at DESC;
```

---

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Verify credentials
psql -U flight_user -d flight_tracker
```

### Database Not Found

```bash
# List databases
psql -U postgres -l

# Recreate if needed
createdb -U flight_user flight_tracker
```

### Data Migration Failed

```bash
# Restore SQLite
rm /path/to/data.db
# Restore from backup
```

---

## Performance Tips

### Indexes

Add indexes for common queries:

```sql
CREATE INDEX idx_flights_airline ON flights(airline);
CREATE INDEX idx_flights_created_at ON flights(created_at);
CREATE INDEX idx_alerts_airline ON alerts(airline);
CREATE INDEX idx_price_history_airline_date ON price_history(airline, date);
```

### Connection Pooling

```python
from sqlalchemy.pool import QueuePool

SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 3600,
}
```

### Query Optimization

Use SQLAlchemy's lazy loading wisely:

```python
# Load related data
flights = Flight.query.options(
    joinedload(Flight.collection)
).all()
```

---

## Data Export

### Export to CSV

```python
import csv
from models import Flight

flights = Flight.query.all()

with open('flights.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['airline', 'price', 'departure', 'arrival', 'stops'])
    for flight in flights:
        writer.writerow([flight.airline, flight.price, flight.departure, flight.arrival, flight.stops])
```

### Export to JSON

```python
import json
from models import Flight

flights = Flight.query.all()

with open('flights.json', 'w') as f:
    json.dump([f.to_dict() for f in flights], f)
```

---

## Questions?

- Check [CONTRIBUTING.md](../CONTRIBUTING.md)
- Open a [GitHub Issue](https://github.com/garciapn/flight-tracker/issues)
