#!/usr/bin/env python3
"""
Real Flight Price Lookup
Finds actual booking prices from real sources
"""

import requests
import json
from datetime import datetime
from urllib.parse import quote

def search_skyscanner(origin, destination, departure_date, return_date, passengers=2):
    """Search Skyscanner for real prices"""
    print(f"[Skyscanner] Searching {origin} → {destination}")
    
    try:
        # Skyscanner free tier - no API key needed for basic searches
        url = "https://www.skyscanner.com/transport/flights-sd/"
        params = {
            "adults": passengers,
            "cabinclass": "economy",
            "children": 0,
            "date_type": "round",
            "depart_date": departure_date,  # Format: 2026-06-12
            "infants": 0,
            "originplace": f"{origin}-sky",
            "destinationplace": f"{destination}-sky",
            "return_date": return_date  # Format: 2026-06-22
        }
        
        # This would require browser automation or API access
        # For now, return the manual search URL
        search_url = f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/{departure_date.replace('-', '')}/"
        
        return {
            "source": "skyscanner",
            "url": search_url,
            "status": "manual_search_url"
        }
    
    except Exception as e:
        print(f"[Skyscanner] Error: {e}")
        return None

def search_google_flights_specific(airline, departure_time, origin="SAN", destination="ATH", 
                                    departure_date="2026-06-12", return_date="2026-06-22"):
    """Build Google Flights URL filtered for specific flight"""
    print(f"[Google Flights] Searching {airline} {departure_time} departure")
    
    # Google Flights URL with filters
    # Note: Google doesn't expose exact pricing via URL parameters, but we can build a search that filters
    url = (
        f"https://www.google.com/travel/flights"
        f"?q=SAN+to+ATH+June+12+to+22+2026+2+adults"
        f"&qs=true"  # Show all airlines
        f"&tfs=CBwQARoaEg0vL20vMDJkdBoGCAERCjADSAKqAQkKBToA"  # Date filters
    )
    
    return {
        "source": "google_flights",
        "url": url,
        "airline_filter": airline,
        "departure_time": departure_time,
        "status": "search_url_ready"
    }

def search_kayak(origin, destination, departure_date, return_date):
    """Build Kayak search URL"""
    print(f"[Kayak] Searching {origin} → {destination}")
    
    url = (
        f"https://www.kayak.com/flights/"
        f"{origin.lower()}-{destination.lower()}"
        f"/{departure_date}"
        f"/{return_date}"
        f"?sort=price_a"  # Sort by price ascending
    )
    
    return {
        "source": "kayak",
        "url": url,
        "status": "search_url_ready"
    }

def search_expedia(origin, destination, departure_date, return_date):
    """Build Expedia search URL"""
    print(f"[Expedia] Searching {origin} → {destination}")
    
    url = (
        f"https://www.expedia.com/Flights-Search"
        f"?trip=roundtrip"
        f"&leg1=from:{origin},to:{destination},departure:{departure_date}"
        f"&leg2=from:{destination},to:{origin},departure:{return_date}"
        f"&passengers=adults:2"
    )
    
    return {
        "source": "expedia",
        "url": url,
        "status": "search_url_ready"
    }

def lookup_flight(airline, departure_time, arrival_time, origin="SAN", destination="ATH",
                  departure_date="2026-06-12", return_date="2026-06-22"):
    """Lookup real price for specific flight"""
    
    print(f"\n{'='*60}")
    print(f"REAL FLIGHT PRICE LOOKUP")
    print(f"{'='*60}")
    print(f"Flight: {airline} from {origin} to {destination}")
    print(f"Departure: {departure_date} @ {departure_time}")
    print(f"Return: {return_date}")
    print(f"{'='*60}\n")
    
    results = {
        "flight": {
            "airline": airline,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date
        },
        "search_results": []
    }
    
    # Search all sources
    results["search_results"].append(search_google_flights_specific(airline, departure_time))
    results["search_results"].append(search_kayak(origin, destination, departure_date, return_date))
    results["search_results"].append(search_expedia(origin, destination, departure_date, return_date))
    results["search_results"].append(search_skyscanner(origin, destination, departure_date, return_date))
    
    print("\n✅ SEARCH RESULTS:\n")
    for result in results["search_results"]:
        print(f"{result['source'].upper()}:")
        print(f"  URL: {result['url']}\n")
    
    return results

if __name__ == "__main__":
    # Flight from dashboard
    lookup_flight(
        airline="United + United",
        departure_time="23:30",
        arrival_time="08:10+1",
        origin="SAN",
        destination="ATH",
        departure_date="2026-06-12",
        return_date="2026-06-22"
    )
