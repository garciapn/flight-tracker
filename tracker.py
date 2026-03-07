#!/usr/bin/env python3
"""
Flight Tracker - Runs via cron 2x daily (8am & 8pm PST)
Scrapes Google Flights, tracks prices, generates alerts
"""
import sqlite3
import json
import os
from datetime import datetime
import subprocess

DB_PATH = "/Users/gerald/.openclaw/workspace/flight-tracker/flights.db"
CONFIG_PATH = "/Users/gerald/.openclaw/workspace/flight-tracker/config.json"
RESULTS_PATH = "/Users/gerald/.openclaw/workspace/flight-tracker/latest_results.json"

# Flight parameters
TRIP = {
    "origin": "SAN",
    "destination": "ATH",
    "depart_date": "2025-06-12",
    "return_date": "2025-06-22",
    "passengers": 2,
    "max_layovers": 1,
    "preferred_arrival_window": "06:00-14:00"  # Morning to afternoon
}

def load_config():
    """Load or create config with price thresholds"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    
    default_config = {
        "price_alert_threshold": 2500,  # Alert if best price < $2500/person (realistic)
        "check_frequency": "twice_daily",
        "check_times": ["08:00", "20:00"],
        "timezone": "America/Los_Angeles",
        "amex_points_budget": 250000,
        "min_amex_value": 0.02  # 2 cents per point
    }
    
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(default_config, f, indent=2)
    return default_config

def parse_flights_from_page_text(page_text):
    """Parse individual flight details from Google Flights page text"""
    import re
    flights = []
    
    if not page_text:
        return flights
    
    # Split by "round trip" to isolate each flight block
    blocks = page_text.split('round trip')
    
    for block in blocks[:-1]:  # Last split is trailing text
        try:
            # Extract times: "7:00 AM – 10:10 AM+1"
            time_match = re.search(
                r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[\–\-–—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM)(?:\+\d)?)',
                block
            )
            if not time_match:
                continue
            
            depart_time = time_match.group(1).strip()
            arrive_time = time_match.group(2).strip()
            
            # Extract airline
            known_airlines = [
                'Air Canada', 'United', 'Alaska', 'American', 'British Airways',
                'Lufthansa', 'Swiss', 'Delta', 'Iberia', 'Aegean', 'KLM',
                'Virgin Atlantic', 'Finnair', 'Brussels Airlines', 'Turkish Airlines',
                'Emirates', 'Qatar Airways', 'TAP Air Portugal'
            ]
            airlines_found = [a for a in known_airlines if a in block]
            airline = ', '.join(airlines_found) if airlines_found else 'Unknown'
            
            # Extract duration: "17 hr 10 min"
            dur_match = re.search(r'(\d+)\s+hr(?:\s+(\d+)\s+min)?', block)
            if dur_match:
                hrs = dur_match.group(1)
                mins = dur_match.group(2) or '0'
                duration = f"{hrs}h {mins}m"
            else:
                duration = 'N/A'
            
            # Extract stops and layover: "1 stop\n2 hr 34 min YUL"
            stops_match = re.search(r'(\d+)\s+stop', block)
            num_stops = int(stops_match.group(1)) if stops_match else 1
            
            # Layover details: duration + airport code after "stop"
            layover_match = re.search(
                r'\d+\s+stop\s+(\d+\s+hr\s+\d+\s+min)\s+([A-Z]{3})',
                block
            )
            if layover_match:
                layover_duration = layover_match.group(1).replace('hr', 'h').replace('min', 'm').replace('  ', ' ')
                layover_city = layover_match.group(2)
            else:
                # Try without minutes: "6 hr LHR"
                layover_match2 = re.search(r'\d+\s+stop\s+(\d+\s+hr)\s+([A-Z]{3})', block)
                if layover_match2:
                    layover_duration = layover_match2.group(1).replace('hr', 'h')
                    layover_city = layover_match2.group(2)
                else:
                    layover_duration = ''
                    layover_city = ''
            
            # Extract price: "$2,403"
            price_match = re.search(r'\$([0-9,]+)', block)
            if not price_match:
                continue
            price = int(price_match.group(1).replace(',', ''))
            
            flights.append({
                "airline": airline,
                "departure": depart_time,
                "arrival": arrive_time,
                "duration": duration,
                "layovers": num_stops,
                "layover_city": layover_city,
                "layover_duration": layover_duration,
                "price": price,
                "class": "economy"
            })
            
        except Exception as e:
            continue
    
    # Sort by price
    flights.sort(key=lambda f: f['price'])
    return flights

def query_flights():
    """
    Query Google Flights using the working scraper.
    Calls scraper-final.js then parses the saved page text for flight details.
    """
    import subprocess
    
    BASE = "/Users/gerald/.openclaw/workspace/flight-tracker"
    PAGE_TEXT_FILE = os.path.join(BASE, "data", "page-text-latest.txt")
    
    try:
        print("🔍 Running flight scraper...")
        result = subprocess.run(
            ["node", "scraper-final.js"],
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.returncode != 0:
            print(f"⚠️ Scraper error: {result.stderr}")
            return None
        
        # Load the data file the scraper just wrote
        data_dir = os.path.join(BASE, "data")
        today = datetime.now().strftime("%Y-%m-%d")
        data_file = os.path.join(data_dir, f"{today}.json")
        
        if not os.path.exists(data_file):
            print(f"❌ No data file found at {data_file}")
            return None
        
        with open(data_file) as f:
            data = json.load(f)
        
        stats = data.get('stats', {})
        
        # Parse actual flight details from saved page text
        page_text = ''
        if os.path.exists(PAGE_TEXT_FILE):
            with open(PAGE_TEXT_FILE) as f:
                page_text = f.read()
        
        flights = parse_flights_from_page_text(page_text)
        
        if not flights:
            print("⚠️ Could not parse individual flights from page text")
            # Fallback: single generic entry
            flights = [{
                "airline": "Best Available",
                "departure": "Various",
                "arrival": "Various", 
                "duration": "N/A",
                "layovers": 1,
                "layover_city": "",
                "layover_duration": "",
                "price": stats.get('min', 0),
                "class": "economy"
            }]
        
        print(f"✅ Parsed {len(flights)} flights, best: ${flights[0]['price'] if flights else 'N/A'}")
        
        results = {
            "timestamp": data.get('timestamp', datetime.now().isoformat()),
            "stats": stats,
            "trips": {
                "2026-06-12": {
                    "flights": flights,
                    "best_price": stats.get('min', flights[0]['price'] if flights else 0),
                    "average_price": stats.get('avg', 0),
                    "price_count": stats.get('count', len(flights))
                }
            }
        }
        
        return results
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timeout (>90s)")
        return None
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return None

def store_flights(results):
    """Store flight data in SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for dep_date, day_data in results["trips"].items():
        for flight in day_data["flights"]:
            try:
                cursor.execute("""
                INSERT INTO flights 
                (departure_date, departure_time, arrival_time, duration, price, 
                 airline, layovers, layover_duration, departure_airport, arrival_airport)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dep_date,
                    flight["departure"],
                    flight["arrival"],
                    flight["duration"],
                    flight["price"],
                    flight["airline"],
                    flight["layovers"],
                    flight.get("layover_city", ""),
                    "SAN",
                    "ATH"
                ))
            except sqlite3.IntegrityError:
                pass  # Duplicate, skip
        
        # Store daily summary
        best_price = day_data.get("best_price") or min([f["price"] for f in day_data.get("flights", [])] or [0])
        avg_price = day_data.get("average_price") or sum([f["price"] for f in day_data.get("flights", [])] or [0]) / (len(day_data.get("flights", [])) or 1)
        
        cursor.execute("""
        INSERT INTO price_history (departure_date, best_price, average_price, flight_count)
        VALUES (?, ?, ?, ?)
        """, (
            dep_date,
            best_price,
            avg_price,
            len(day_data.get("flights", []))
        ))
    
    conn.commit()
    conn.close()

def check_alerts(config):
    """Check if price dropped below threshold and create alerts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Handle both old and new config formats
    if "price_alert_threshold" in config:
        threshold = config["price_alert_threshold"]
    elif "alerts" in config and "targetPricePerPerson" in config["alerts"]:
        threshold = config["alerts"]["targetPricePerPerson"] or 1200
    else:
        threshold = 1200
    
    # Get best price from last 24h
    cursor.execute("""
    SELECT departure_date, best_price 
    FROM price_history 
    WHERE date_tracked > datetime('now', '-1 day')
    ORDER BY best_price ASC LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result and result[1] < threshold:
        dep_date, price = result
        airline = "Best Available"
        cursor.execute("""
        INSERT INTO alerts (departure_date, price_threshold, actual_price, airline, status)
        VALUES (?, ?, ?, ?, 'triggered')
        """, (dep_date, threshold, price, airline))
        conn.commit()
        return {"alert": True, "price": price, "airline": airline, "date": dep_date}
    
    conn.close()
    return {"alert": False}

def generate_report():
    """Generate weekly trend report"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        departure_date,
        best_price,
        average_price,
        flight_count
    FROM price_history
    WHERE date_tracked > datetime('now', '-7 days')
    ORDER BY departure_date
    """)
    
    rows = cursor.fetchall()
    trends = {
        "period": "last_7_days",
        "trips": [
            {
                "date": row[0],
                "best_price": row[1],
                "average_price": row[2],
                "flight_options": row[3]
            }
            for row in rows
        ] if rows else []
    }
    
    conn.close()
    return trends

def main():
    print(f"[{datetime.now()}] Flight Tracker Running...")
    
    config = load_config()
    results = query_flights()
    store_flights(results)
    alert = check_alerts(config)
    trends = generate_report()
    
    # Save latest results to latest_results.json
    output = {
        "timestamp": results["timestamp"],
        "latest_flights": results,
        "alert": alert,
        "trends": trends
    }
    
    with open(RESULTS_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Also save to data/YYYY-MM-DD.json for Flask dashboard compatibility
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = os.path.join(os.path.dirname(RESULTS_PATH), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    data_file = os.path.join(data_dir, f"{today}.json")
    
    # Get the first trip date from results
    trip_date = list(results.get("trips", {}).keys())[0] if results.get("trips") else "2026-06-12"
    trip_data = results["trips"].get(trip_date, {})
    
    with open(data_file, 'w') as f:
        json.dump({
            "timestamp": results["timestamp"],
            "stats": results.get("stats", {
                "count": trip_data.get("price_count", 1),
                "min": trip_data.get("best_price", 0),
                "max": trip_data.get("best_price", 0) + 2000,
                "avg": int(trip_data.get("average_price", 0))
            }),
            "flights": trip_data.get("flights", [])
        }, f, indent=2)
    
    print(f"✅ Check complete. Results saved to {RESULTS_PATH}")
    print(f"✅ Dashboard data saved to {data_file}")
    if alert["alert"]:
        print(f"🚨 PRICE ALERT: {alert['airline']} at ${alert['price']} on {alert['date']}")

if __name__ == "__main__":
    main()
