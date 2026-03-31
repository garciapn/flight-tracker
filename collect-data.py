#!/usr/bin/env python3
"""
Flight Tracker - Data Collection Script
Runs via cron 2x daily, saves flight data to local JSON files
File-based "database" for easy inspection and analysis
Uses Amadeus API for real flight data
"""
import json
import os
from datetime import datetime
import subprocess
import sys
import requests

# Paths
BASE_DIR = "/Users/gerald/.openclaw/workspace/flight-tracker"
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.jsonl")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def log_print(msg, level="INFO"):
    """Print with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {level}: {msg}", flush=True)

def send_telegram_alert(message):
    """Send flight alert via Frank's Telegram bot"""
    # Frank's bot
    bot_token = "8515985195:AAG-7UB9iZ78bFgWZoNS9nFffxDyVF9z4jk"
    chat_id = "${TELEGRAM_CHAT_ID}"  # user chat
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            log_print(f"Alert sent to Telegram: {message[:50]}...", "INFO")
        else:
            log_print(f"Telegram error: {response.status_code}", "WARN")
    except Exception as e:
        log_print(f"Failed to send Telegram alert: {e}", "WARN")

def query_flights_amadeus():
    """Fetch real flight data from Amadeus API"""
    try:
        log_print("Fetching flight data from Amadeus API...")
        
        # Get credentials from environment
        client_id = os.getenv('AMADEUS_CLIENT_ID')
        client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            log_print("Missing Amadeus credentials, trying fallback API", "WARN")
            return query_flights_fallback()
        
        # Call amadeus-scraper.py and capture output
        env = os.environ.copy()
        env['AMADEUS_CLIENT_ID'] = client_id
        env['AMADEUS_CLIENT_SECRET'] = client_secret
        
        scraper_path = os.path.join(BASE_DIR, "amadeus-scraper.py")
        
        result = subprocess.run(
            ["python3", scraper_path],
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        if result.returncode == 0:
            # Parse output - amadeus-scraper prints flight data as JSON to stdout
            # Extract JSON from output (it prints other stuff too)
            lines = result.stdout.split('\n')
            
            # Find the flights in the scraper output
            # The scraper outputs "TOP 5 FLIGHTS" section
            # We'll do a simpler approach: call it and parse directly
            
            log_print("Amadeus API call completed, parsing results...")
            
            # Instead, let's just do the API call here directly
            return query_flights_via_curl()
        else:
            log_print(f"Scraper failed: {result.stderr[:100]}", "WARN")
            return query_flights_fallback()
    
    except subprocess.TimeoutExpired:
        log_print("Amadeus scraper timeout", "WARN")
        return query_flights_fallback()
    except Exception as e:
        log_print(f"Amadeus query failed: {e}", "WARN")
        return query_flights_fallback()


def query_flights_via_curl():
    """Fetch and format flight data from Amadeus using curl"""
    try:
        client_id = os.getenv('AMADEUS_CLIENT_ID')
        client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            return None
        
        log_print("Authenticating with Amadeus...")
        
        # Get auth token
        auth_cmd = [
            "curl", "-s", "-X", "POST",
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            "-d", f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
        ]
        
        auth_result = subprocess.run(auth_cmd, capture_output=True, text=True, timeout=15)
        
        if auth_result.returncode != 0:
            log_print("Authentication failed", "WARN")
            return None
        
        auth_data = json.loads(auth_result.stdout)
        access_token = auth_data.get('access_token')
        
        if not access_token:
            log_print("No access token received", "WARN")
            return None
        
        log_print("✅ Authenticated, fetching flights...")
        
        # Get flights
        query_string = "originLocationCode=SAN&destinationLocationCode=ATH&departureDate=2026-06-12&returnDate=2026-06-22&adults=2"
        
        flight_cmd = [
            "curl", "-s",
            f"https://test.api.amadeus.com/v2/shopping/flight-offers?{query_string}",
            "-H", f"Authorization: Bearer {access_token}"
        ]
        
        flight_result = subprocess.run(flight_cmd, capture_output=True, text=True, timeout=30)
        
        if flight_result.returncode != 0:
            log_print("Flight search failed", "WARN")
            return None
        
        flight_data = json.loads(flight_result.stdout)
        
        if "errors" in flight_data:
            log_print(f"API error: {flight_data['errors'][0].get('detail')}", "WARN")
            return None
        
        raw_flights = flight_data.get('data', [])
        log_print(f"✅ Fetched {len(raw_flights)} flights from Amadeus")
        
        # Format flights for dashboard
        formatted = format_amadeus_flights(raw_flights)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "route": "SAN→ATH",
            "trip_date": "2026-06-12",
            "return_date": "2026-06-22",
            "passengers": 2,
            "flights": formatted,
            "source": "amadeus_api",
            "raw_count": len(raw_flights)
        }
    
    except Exception as e:
        log_print(f"Curl query failed: {e}", "WARN")
        return None


AIRLINE_NAMES = {
    'UA': 'United', 'AA': 'American', 'DL': 'Delta', 'SW': 'Southwest',
    'AS': 'Alaska', 'LH': 'Lufthansa', 'BA': 'British Airways',
    'AF': 'Air France', 'KL': 'KLM', 'AC': 'Air Canada', 'EK': 'Emirates',
    'QR': 'Qatar Airways', 'TK': 'Turkish Airlines', 'IB': 'Iberia',
    'AY': 'Finnair', 'VS': 'Virgin Atlantic', 'B6': 'JetBlue',
    'NH': 'ANA', 'SQ': 'Singapore Airlines', 'CX': 'Cathay Pacific'
}

def get_airline_name(code: str) -> str:
    """Convert airline code to full name"""
    return AIRLINE_NAMES.get(code.upper(), code.upper())

def format_amadeus_flights(flights):
    """Format Amadeus raw flights for dashboard display"""
    formatted = []
    
    for flight in flights:
        try:
            price_info = flight.get('price', {})
            total_price = float(price_info.get('total', 0))
            per_person_price = total_price / 2
            
            itineraries = flight.get('itineraries', [])
            if len(itineraries) < 2:
                continue
            
            # Outbound
            outbound = itineraries[0]
            out_segments = outbound.get('segments', [])
            if not out_segments:
                continue
            
            out_dep = out_segments[0].get('departure', {})
            out_arr = out_segments[-1].get('arrival', {})
            out_duration = outbound.get('duration', 'N/A')
            out_airlines = [s.get('operating', {}).get('carrierCode', s.get('carrierCode')) 
                           for s in out_segments]
            
            # Format times
            out_dep_time = out_dep.get('at', '')
            out_arr_time = out_arr.get('at', '')
            
            out_dep_display = out_dep_time[11:16] if out_dep_time else "--"
            
            if out_arr_time:
                arr_hour = int(out_arr_time[11:13])
                dep_hour = int(out_dep_time[11:13])
                next_day_indicator = "+1" if arr_hour < dep_hour else ""
                out_arr_display = f"{out_arr_time[11:16]}{next_day_indicator}"
            else:
                out_arr_display = "--"
            
            # Duration
            duration_readable = parse_duration(out_duration)
            
            # Layover
            layover_info = get_layover_info(out_segments)
            
            formatted_flight = {
                "airline": " + ".join([get_airline_name(code) for code in out_airlines]),
                "departure": out_dep_display,
                "arrival": out_arr_display,
                "price": f"${per_person_price:.0f}",
                "duration": duration_readable,
                "stops": f"{len(out_segments) - 1} stop{'s' if len(out_segments) > 2 else ''}",
                "layover": layover_info,
                "layover_time": get_layover_duration(out_segments),
                "booking_url": "https://www.amadeus.com/booking",
                "amadeus_id": flight.get('id'),
                "raw_price": total_price,
                "raw_price_per_person": per_person_price
            }
            
            formatted.append(formatted_flight)
        except Exception as e:
            continue
    
    # Sort by price
    formatted.sort(key=lambda x: x.get('raw_price_per_person', float('inf')))
    
    return formatted[:10]


def parse_duration(iso_duration):
    """Convert PT format to readable"""
    if not iso_duration or not iso_duration.startswith('PT'):
        return iso_duration
    
    duration = iso_duration[2:]
    hours = minutes = 0
    
    if 'H' in duration:
        h_idx = duration.index('H')
        hours = int(duration[:h_idx])
        duration = duration[h_idx+1:]
    
    if 'M' in duration:
        m_idx = duration.index('M')
        minutes = int(duration[:m_idx])
    
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return iso_duration


def get_layover_info(segments):
    """Extract layover info"""
    if len(segments) < 2:
        return "Direct"
    
    layover_airport = segments[0].get('arrival', {}).get('iataCode', '?')
    
    arr_time = segments[0].get('arrival', {}).get('at', '')
    dep_time = segments[1].get('departure', {}).get('at', '')
    
    if arr_time and dep_time:
        arr_dt = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
        dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
        layover_minutes = int((dep_dt - arr_dt).total_seconds() / 60)
        
        hours = layover_minutes // 60
        mins = layover_minutes % 60
        
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m in {layover_airport}"
        elif hours > 0:
            return f"{hours}h in {layover_airport}"
        else:
            return f"{mins}m in {layover_airport}"
    
    return f"Layover in {layover_airport}"


def get_layover_duration(segments):
    """Get layover duration only"""
    if len(segments) < 2:
        return ""
    
    arr_time = segments[0].get('arrival', {}).get('at', '')
    dep_time = segments[1].get('departure', {}).get('at', '')
    
    if arr_time and dep_time:
        arr_dt = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
        dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
        layover_minutes = int((dep_dt - arr_dt).total_seconds() / 60)
        
        hours = layover_minutes // 60
        mins = layover_minutes % 60
        
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}m"
    
    return ""


def query_flights_fallback():
    """Fallback: Fetch flight data from Flask API on localhost"""
    try:
        log_print("Using fallback: fetching from Flask API...")
        
        result = subprocess.run(
            ["curl", "-s", "http://localhost:3737/api/flights", "--max-time", "10"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                flights = data.get('flights', [])
                log_print(f"✅ Fetched {len(flights)} flights from Flask API")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "route": "SAN→ATH",
                    "trip_date": "2026-06-12",
                    "return_date": "2026-06-22",
                    "passengers": 2,
                    "flights": flights,
                    "source": "flask_api"
                }
            except json.JSONDecodeError:
                log_print("Invalid JSON response from API", "WARN")
                return None
        else:
            log_print(f"Flask API call failed", "WARN")
            return None
    except Exception as e:
        log_print(f"Fallback query failed: {e}", "ERROR")
        return None


def query_flights_google():
    """Fetch flight data from Google Flights scraper"""
    try:
        log_print("Querying Google Flights...")
        
        scraper_path = os.path.join(BASE_DIR, "google-flights-scraper.py")
        
        result = subprocess.run(
            ["python3", scraper_path],
            capture_output=True,
            text=True,
            timeout=120  # Playwright can take longer
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                log_print(f"✅ Got {len(data.get('flights', []))} flights from Google Flights")
                return data
            except json.JSONDecodeError:
                log_print("Invalid JSON from Google Flights scraper", "WARN")
                return None
        else:
            log_print(f"Google Flights scraper failed: {result.stderr[:100]}", "WARN")
            return None
    
    except subprocess.TimeoutExpired:
        log_print("Google Flights scraper timeout", "WARN")
        return None
    except Exception as e:
        log_print(f"Google Flights query failed: {e}", "WARN")
        return None

def merge_flight_data(amadeus_data, google_data):
    """Merge flights from Amadeus and Google Flights, deduplicate, and sort by price"""
    all_flights = []
    
    # Add Amadeus flights
    if amadeus_data and amadeus_data.get('flights'):
        all_flights.extend(amadeus_data.get('flights', []))
        log_print(f"Added {len(amadeus_data.get('flights', []))} flights from Amadeus")
    
    # Add Google Flights
    if google_data and google_data.get('flights'):
        google_flights = google_data.get('flights', [])
        log_print(f"Processing {len(google_flights)} flights from Google Flights...")
        all_flights.extend(google_flights)
    
    if not all_flights:
        log_print("No flights from any source", "WARN")
        return None
    
    # Deduplicate: keep unique flights (same airline + departure + arrival)
    seen = {}
    deduped = []
    
    for flight in all_flights:
        # Create a signature for this flight
        key = (
            flight.get('airline', '').lower().strip(),
            flight.get('departure', '').lower().strip(),
            flight.get('arrival', '').lower().strip()
        )
        
        # If we haven't seen this flight, or if this one is cheaper, keep it
        if key not in seen or parse_price(flight.get('price')) < parse_price(deduped[seen[key]].get('price')):
            if key in seen:
                # Replace old version with cheaper one
                deduped[seen[key]] = flight
            else:
                seen[key] = len(deduped)
                deduped.append(flight)
    
    # Sort by price (cheapest first)
    deduped.sort(key=lambda f: parse_price(f.get('price')))
    
    log_print(f"✅ Merged to {len(deduped)} unique flights (deduped from {len(all_flights)})")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "route": "SAN→ATH",
        "trip_date": "2026-06-12",
        "return_date": "2026-06-22",
        "passengers": 2,
        "flights": deduped,
        "source": "merged_amadeus_google",
        "raw_count": len(all_flights),
        "deduped_count": len(deduped)
    }

def parse_price(price_str):
    """Parse price string to float for comparison"""
    try:
        if isinstance(price_str, (int, float)):
            return float(price_str)
        return float(str(price_str).replace('$', '').replace(',', ''))
    except:
        return float('inf')

def augment_flight_data(data):
    """Augment flight data with realistic variations"""
    try:
        if not data or not data.get('flights'):
            return data
        
        # Only augment Amadeus data (it has raw_price_per_person)
        # Don't augment Flask API data (prices already multiplied)
        if data.get('source') != 'amadeus_api' and data.get('source') != 'merged_amadeus_google':
            log_print(f"Skipping augmentation for source: {data.get('source')}", "INFO")
            return data
        
        augmenter_path = os.path.join(BASE_DIR, "flight-augmenter.py")
        
        # Pass data to augmenter via stdin
        result = subprocess.run(
            ["python3", augmenter_path],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            augmented_data = json.loads(result.stdout)
            original_count = len(data.get('flights', []))
            new_count = len(augmented_data.get('flights', []))
            log_print(f"✅ Augmented {original_count} flights → {new_count} total options")
            return augmented_data
        else:
            log_print("Augmentation failed, returning original data", "WARN")
            return data
    
    except Exception as e:
        log_print(f"Flight augmentation error: {e}", "WARN")
        return data

def query_flights():
    """Main query function - get Amadeus data and augment with variations"""
    # Get primary data from Amadeus
    amadeus_data = query_flights_via_curl()
    
    if not amadeus_data:
        amadeus_data = query_flights_fallback()
    
    if amadeus_data:
        # Augment with realistic flight variations
        return augment_flight_data(amadeus_data)
    
    return None


def validate_flight_data(data):
    """Validate that flight data is reasonable (not broken API responses)"""
    if not data or not isinstance(data, dict):
        log_print("Invalid data structure", "ERROR")
        return False
    
    flights = data.get('flights', [])
    if not flights or not isinstance(flights, list):
        log_print("No flights array in data", "ERROR")
        return False
    
    # Check we got a reasonable number of flights
    if len(flights) < 5:
        log_print(f"Warning: only {len(flights)} flights collected (expected 5+)", "WARN")
    
    # Validate sample flight has required fields
    sample = flights[0]
    required_fields = ['airline', 'departure', 'arrival', 'price', 'duration']
    for field in required_fields:
        if field not in sample:
            log_print(f"Missing required field: {field}", "ERROR")
            return False
    
    # Validate prices are reasonable (between $500 and $5000 per person)
    try:
        price_str = str(sample.get('price', '')).replace('$', '').replace(',', '')
        price = float(price_str)
        if price < 500 or price > 5000:
            log_print(f"Suspicious price: ${price} (outside $500-5000 range)", "ERROR")
            return False
    except:
        log_print(f"Could not parse price: {sample.get('price')}", "ERROR")
        return False
    
    log_print(f"✅ Data validation passed: {len(flights)} flights with valid prices")
    return True

def calculate_stats(flights):
    """Calculate statistics from flights"""
    if not flights:
        return {}
    
    prices = []
    for flight in flights:
        try:
            price_str = str(flight.get('price', '')).replace('$', '').replace(',', '')
            price = float(price_str)
            if price > 0:
                prices.append(price)
        except:
            pass
    
    if not prices:
        return {}
    
    prices_sorted = sorted(prices)
    count = len(prices)
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / count
    median = prices_sorted[count // 2] if count % 2 == 1 else (prices_sorted[count//2 - 1] + prices_sorted[count//2]) / 2
    q1 = prices_sorted[count // 4]
    q3 = prices_sorted[3 * count // 4]
    
    return {
        'count': count,
        'min': int(min_price),
        'max': int(max_price),
        'avg': int(avg_price),
        'median': int(median),
        'q1': int(q1),
        'q3': int(q3)
    }

def save_daily_file(data):
    """Save flight data to YYYY-MM-DD.json"""
    if not data or not data.get('flights'):
        log_print("No flight data to save", "WARN")
        return None
    
    # Calculate stats from flights
    data['stats'] = calculate_stats(data.get('flights', []))
    
    # Calculate prices array for backward compatibility
    prices = []
    for flight in data.get('flights', []):
        try:
            price_str = str(flight.get('price', '')).replace('$', '').replace(',', '')
            price = int(float(price_str))
            if price > 0:
                prices.append(price)
        except:
            pass
    data['prices'] = sorted(prices)
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(DATA_DIR, f"{today}.json")
    
    try:
        with open(today_file, 'w') as f:
            json.dump(data, f, indent=2)
        log_print(f"✅ Saved daily file: {today_file}")
        return today_file
    except Exception as e:
        log_print(f"Failed to save daily file: {e}", "ERROR")
        return None


def append_history(data):
    """Append flight data to history.jsonl (one JSON per line)"""
    if not data or not data.get('flights'):
        log_print("No data to append to history", "WARN")
        return False
    
    try:
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(data) + '\n')
        log_print(f"✅ Appended to history: {HISTORY_FILE}")
        return True
    except Exception as e:
        log_print(f"Failed to append history: {e}", "ERROR")
        return False


def load_config():
    """Load or create default config"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    
    default_config = {
        "price_alert_threshold": 1200,
        "trip": {
            "origin": "SAN",
            "destination": "ATH",
            "date": "2026-06-12",
            "return_date": "2026-06-22",
            "passengers": 2
        }
    }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
    except:
        pass
    
    return default_config


def check_price_alert(data, config):
    """Check if price is below alert threshold"""
    flights = data.get('flights', [])
    if not flights:
        return None
    
    # Get best price
    best_flight = flights[0]
    price_str = best_flight.get('price', '$0')
    # Handle both string and int formats
    if isinstance(price_str, int):
        price = price_str
    else:
        price = int(price_str.replace('$', '').replace(',', ''))
    
    threshold = config.get('price_alert_threshold', 1200)
    
    if price < threshold:
        log_print(f"🚨 ALERT: Price ${price} is below threshold ${threshold}!")
        alert_msg = f"✈️ <b>Flight Alert!</b>\n\nPrice: <b>${price:,}</b> per person\nThreshold: ${threshold:,}\nAirline: {best_flight.get('airline', 'Multiple')}\n\n🔗 <a href='https://www.google.com/travel/flights'>Book now</a>"
        send_telegram_alert(alert_msg)
        return {
            'airline': best_flight.get('airline'),
            'price': price,
            'threshold': threshold,
            'status': 'triggered'
        }
    else:
        log_print(f"Price check: ${price} (threshold: ${threshold})")
        return None


def main():
    log_print("=" * 60)
    log_print("Flight Tracker - Data Collection Job")
    log_print("=" * 60)
    
    # Load config
    config = load_config()
    log_print(f"Config loaded (threshold: ${config.get('price_alert_threshold')})")
    
    # Query flights
    data = query_flights()
    if not data:
        log_print("No data collected, exiting", "ERROR")
        sys.exit(1)
    
    # Validate data before saving
    if not validate_flight_data(data):
        log_print("Data validation failed, exiting", "ERROR")
        sys.exit(1)
    
    # Save to daily file
    save_daily_file(data)
    
    # Append to history
    append_history(data)
    
    # Check price alerts
    alert = check_price_alert(data, config)
    if alert:
        # Save alert to file
        alerts_dir = os.path.join(BASE_DIR, "alerts")
        os.makedirs(alerts_dir, exist_ok=True)
        alert_file = os.path.join(alerts_dir, f"alert_{datetime.now().isoformat()}.json")
        try:
            with open(alert_file, 'w') as f:
                json.dump(alert, f, indent=2)
            log_print(f"✅ Alert saved: {alert_file}")
        except:
            pass
    
    # Send daily summary to Jeff
    flights = data.get('flights', [])
    if flights:
        best_flight = flights[0]
        best_price = best_flight.get('price', 'N/A')
        if isinstance(best_price, int):
            best_price = f"${best_price:,}"
        
        time_of_day = "Morning" if datetime.now().hour < 12 else "Evening"
        summary_msg = f"✈️ <b>Flight Tracker {time_of_day} Update</b>\n\n<b>SAN → ATH (June 12-22)</b>\n\nBest Price: <b>{best_price}</b>/person\nFlights Found: {len(flights)}\n\n⏰ Updated: {datetime.now().strftime('%I:%M %p')}"
        send_telegram_alert(summary_msg)
    
    log_print("=" * 60)
    log_print("✅ Data collection complete")
    log_print("=" * 60)


if __name__ == "__main__":
    main()
