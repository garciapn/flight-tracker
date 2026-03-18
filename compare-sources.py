#!/usr/bin/env python3
"""
Compare Google Flights vs Amadeus results
Analyze price discrepancies and data quality
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import statistics

def load_results(filepath: str) -> Dict:
    """Load JSON results"""
    path = Path(filepath)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None

def compare_sources() -> Dict:
    """Compare Google Flights and Amadeus"""
    
    # Load Amadeus baseline
    amadeus_data = load_results("data/unified-results.json")
    if not amadeus_data:
        print("ERROR: Amadeus baseline not found at data/unified-results.json")
        return {}
    
    amadeus_flights = amadeus_data.get("top_15", [])
    amadeus_count = len(amadeus_flights)
    amadeus_prices = [f["price"] for f in amadeus_flights]
    
    # Load Google Flights
    google_data = load_results("data/google-flights-latest.json")
    google_flights = google_data.get("top_15", []) if google_data else []
    google_count = len(google_flights)
    
    print("=" * 80)
    print("FLIGHT SOURCE COMPARISON REPORT")
    print("=" * 80)
    print(f"Route: SAN → ATH (June 12-22, 2 passengers)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Summary
    print("📊 DATA COLLECTION SUMMARY")
    print("-" * 80)
    print(f"Amadeus:      {amadeus_count} flights")
    print(f"Google:       {google_count} flights")
    print()
    
    if amadeus_count > 0:
        print(f"Amadeus Price Range: ${min(amadeus_prices):.2f} - ${max(amadeus_prices):.2f}")
        print(f"Amadeus Avg Price:   ${statistics.mean(amadeus_prices):.2f}")
        print(f"Amadeus Median:      ${statistics.median(amadeus_prices):.2f}")
    print()
    
    # Matching analysis
    if google_count > 0 and amadeus_count > 0:
        google_prices = [f["price"] for f in google_flights]
        
        # Count price matches (within $50)
        matches = 0
        close_matches = 0  # within $100
        
        for g_price in google_prices:
            for a_price in amadeus_prices:
                if abs(g_price - a_price) < 50:
                    matches += 1
                    break
            else:
                if any(abs(g_price - a_price) < 100 for a_price in amadeus_prices):
                    close_matches += 1
        
        print("🔗 PRICE MATCHING")
        print("-" * 80)
        print(f"Exact matches (±$50):     {matches}/{google_count}")
        print(f"Close matches (±$100):    {close_matches}/{google_count}")
        print(f"Match rate:               {(matches/max(1, google_count)*100):.1f}%")
        print()
        
        # Data quality
        google_with_airline = sum(1 for f in google_flights if f.get("airline") and f["airline"] != "N/A")
        google_with_duration = sum(1 for f in google_flights if f.get("duration") and f["duration"] != "N/A")
        google_with_stops = sum(1 for f in google_flights if "stops" in f)
        
        amadeus_with_airline = sum(1 for f in amadeus_flights if f.get("airline") and f["airline"] != "N/A")
        amadeus_with_duration = sum(1 for f in amadeus_flights if f.get("duration") and f["duration"] != "N/A")
        amadeus_with_stops = sum(1 for f in amadeus_flights if "stops" in f)
        
        print("📋 DATA QUALITY")
        print("-" * 80)
        print(f"{'Field':<20} {'Google':<15} {'Amadeus':<15}")
        print(f"{'-'*20} {'-'*15} {'-'*15}")
        print(f"{'Airline codes':<20} {google_with_airline}/{google_count:<14} {amadeus_with_airline}/{amadeus_count}")
        print(f"{'Duration':<20} {google_with_duration}/{google_count:<14} {amadeus_with_duration}/{amadeus_count}")
        print(f"{'Stops':<20} {google_with_stops}/{google_count:<14} {amadeus_with_stops}/{amadeus_count}")
        print()
    
    # Top 5 comparison
    print("💰 TOP 5 CHEAPEST FLIGHTS")
    print("-" * 80)
    
    if amadeus_count > 0:
        print("\nAmadeus Top 5:")
        for i, flight in enumerate(amadeus_flights[:5], 1):
            print(f"  {i}. {flight['airline']:<4s} ${flight['price']:8.2f} - "
                  f"{flight.get('duration', 'N/A')} ({flight.get('stops', '?')} stops)")
    
    if google_count > 0:
        print("\nGoogle Flights Top 5:")
        for i, flight in enumerate(google_flights[:5], 1):
            duration = flight.get('duration', 'N/A')
            stops = flight.get('stops', '?')
            print(f"  {i}. {flight['airline']:<4s} ${flight['price']:8.2f} - "
                  f"{duration} ({stops} stops)")
    
    print()
    
    # Recommendations
    print("🎯 RECOMMENDATIONS")
    print("-" * 80)
    
    if google_count == 0:
        print("✓ AMADEUS AS PRIMARY")
        print("  Google Flights scraping currently blocked by anti-bot detection.")
        print("  Amadeus provides reliable, complete data.")
        print("  Recommendation: Use Amadeus as primary source for now.")
        print("  Future: Implement rotating proxies or service-based approach for Google.")
        recommendation = "amadeus"
    elif google_count > 0 and google_count >= amadeus_count * 0.7:
        matches_rate = (matches / google_count * 100) if google_count > 0 else 0
        if matches_rate > 50:
            print("✓ GOOGLE FLIGHTS AS PRIMARY")
            print(f"  Google Flights found {google_count} flights ({matches_rate:.0f}% price match with Amadeus).")
            print("  Data quality is good and prices are competitive.")
            recommendation = "google"
        else:
            print("⚠️  DUAL SOURCE (Amadeus + Google)")
            print("  Google found flights but prices differ significantly from Amadeus.")
            print("  Recommend using both sources and comparing prices.")
            recommendation = "dual"
    else:
        print("✓ AMADEUS AS PRIMARY + Google FALLBACK")
        print("  Amadeus provides complete, reliable data.")
        print("  Google Flights can be used as a secondary verification source.")
        recommendation = "amadeus-primary"
    
    print()
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "route": "SAN→ATH",
        "summary": {
            "amadeus_flights": amadeus_count,
            "google_flights": google_count,
            "recommendation": recommendation
        },
        "amadeus_stats": {
            "count": amadeus_count,
            "min_price": min(amadeus_prices) if amadeus_prices else None,
            "max_price": max(amadeus_prices) if amadeus_prices else None,
            "avg_price": statistics.mean(amadeus_prices) if amadeus_prices else None,
            "median_price": statistics.median(amadeus_prices) if amadeus_prices else None
        },
        "google_stats": {
            "count": google_count,
            "min_price": min(google_prices) if google_count > 0 else None,
            "max_price": max(google_prices) if google_count > 0 else None,
            "avg_price": statistics.mean(google_prices) if google_count > 0 else None
        },
        "matching_analysis": {
            "exact_matches": matches if google_count > 0 else 0,
            "close_matches": close_matches if google_count > 0 else 0,
            "match_rate_percent": (matches / max(1, google_count) * 100) if google_count > 0 else 0
        }
    }
    
    # Save report
    output_file = Path("data/comparison-report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Report saved to {output_file}")
    
    return report


if __name__ == "__main__":
    compare_sources()
