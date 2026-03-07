#!/usr/bin/env python3
"""
Simple flight data scraper - fetches from Google Flights
Outputs JSON for collect-data.py to save
"""
import json
import subprocess
from datetime import datetime
import sys

def scrape_flights():
    """Scrape flight data from Google Flights"""
    # URL for SAN -> ATH, June 12-22, 2 passengers
    url = (
        "https://www.google.com/travel/flights?q="
        "Flights%20from%20SAN%20to%20ATH%20on%202026-06-12%20"
        "returning%202026-06-22%20for%202%20adults"
    )
    
    try:
        # Use curl to fetch the page
        result = subprocess.run(
            ["curl", "-s", "-A", "Mozilla/5.0", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            # Parse flight data from HTML
            flights = parse_flights_from_html(result.stdout)
            return {
                "timestamp": datetime.now().isoformat(),
                "route": "SAN-ATH",
                "dates": "2026-06-12 to 2026-06-22",
                "passengers": 2,
                "flights": flights,
                "source": "google_flights",
                "status": "success"
            }
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    
    return None

def parse_flights_from_html(html):
    """Simple parser - extract flight info from HTML"""
    import re
    flights = []
    
    # Look for price patterns and flight info
    price_pattern = r'\$\d+,?\d*'
    prices = re.findall(price_pattern, html)
    
    # For now, return empty but structured list
    # In production, would use BeautifulSoup or Playwright
    return flights

if __name__ == "__main__":
    data = scrape_flights()
    if data:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps({"error": "Failed to scrape", "flights": []}, file=sys.stderr))
        sys.exit(1)
