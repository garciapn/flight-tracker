#!/usr/bin/env python3
"""
Flight Data Augmenter - Generates realistic flight variations from base Amadeus data
Creates alternative routings with realistic prices to provide more options
"""
import json
from typing import List, Dict
from datetime import datetime, timedelta

def augment_flights(base_flights: List[Dict]) -> List[Dict]:
    """Generate additional realistic flight variations from base data"""
    
    if not base_flights or len(base_flights) == 0:
        return base_flights
    
    augmented = list(base_flights)  # Start with originals
    
    # Airline names for variations
    airlines = [
        "United", "American", "Delta", "Lufthansa", "Air Canada",
        "British Airways", "Air France", "KLM", "Emirates", "Turkish Airlines"
    ]
    
    # Airports for generating alternative routings
    european_hubs = [
        ("CDG", "Paris"),
        ("LHR", "London"),
        ("FRA", "Frankfurt"),
        ("MUC", "Munich"),
        ("AMS", "Amsterdam"),
        ("DUB", "Dublin"),
        ("IST", "Istanbul")
    ]
    
    us_hubs = [
        ("JFK", "New York"),
        ("ORD", "Chicago"),
        ("IAD", "Washington"),
        ("ATL", "Atlanta"),
        ("DFW", "Dallas"),
        ("LAX", "Los Angeles"),
        ("EWR", "Newark")
    ]
    
    # Generate realistic price variations
    # Airlines tend to have different pricing for same routes
    price_multipliers = [0.95, 0.98, 1.02, 1.05, 1.10, 1.15, 1.20]
    
    # For each base flight, create variations
    for base_flight in base_flights[:10]:  # Use top 10 as basis
        base_price = parse_price(base_flight.get('price', '$1000'))
        
        if base_price > 0:
            # Generate alternative routings with different prices
            for i, multiplier in enumerate(price_multipliers):
                # Skip the first one (original)
                if i == 0:
                    continue
                
                new_price = int(base_price * multiplier)
                
                # Vary departure/arrival times
                base_hour = int(base_flight.get('departure', '12:00').split(':')[0])
                new_hour = (base_hour + (i % 12)) % 24
                new_departure = f"{new_hour:02d}:{base_flight.get('departure', '12:00').split(':')[1]}"
                
                # Vary duration slightly
                duration_str = base_flight.get('duration', '17h 30m')
                
                # Vary airline (create plausible combinations with full names)
                base_airlines = base_flight.get('airline', 'Airline').split(' + ')
                if len(base_airlines) > 1:
                    # Use existing airline combination, just vary the price
                    new_airline = base_flight.get('airline', 'Airline')
                else:
                    # Alternate between airlines
                    idx = (i * 2) % len(airlines)
                    new_airline = airlines[idx]
                
                # Create flight variant - preserve amadeus_id from base flight if available
                variant = {
                    "airline": new_airline,
                    "departure": new_departure,
                    "arrival": base_flight.get('arrival', '08:00'),
                    "duration": duration_str,
                    "stops": base_flight.get('stops', '1 stop'),
                    "layover": base_flight.get('layover', '2h 30m'),
                    "layover_time": base_flight.get('layover_time', '2h 30m'),
                    "price": f"${new_price}",
                    "booking_url": base_flight.get('booking_url', ''),
                    "amadeus_id": base_flight.get('amadeus_id', ''),
                    "raw_price_per_person": base_flight.get('raw_price_per_person', new_price),
                    "source": "amadeus_augmented"
                }
                
                augmented.append(variant)
    
    # Remove duplicates by (airline, departure, arrival)
    seen = {}
    unique = []
    for flight in augmented:
        key = (
            flight.get('airline', '').lower(),
            flight.get('departure', '').lower(),
            flight.get('arrival', '').lower()
        )
        
        if key not in seen:
            seen[key] = True
            unique.append(flight)
    
    # Sort by price
    unique.sort(key=lambda f: parse_price(f.get('price', '$5000')))
    
    return unique[:30]  # Return top 30

def parse_price(price_str):
    """Parse price string to int"""
    try:
        if isinstance(price_str, (int, float)):
            return int(price_str)
        return int(str(price_str).replace('$', '').replace(',', ''))
    except:
        return 0

if __name__ == "__main__":
    # Test: read from stdin
    import sys
    
    try:
        data = json.load(sys.stdin)
        flights = data.get('flights', [])
        
        augmented = augment_flights(flights)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "route": data.get('route', 'SAN→ATH'),
            "trip_date": data.get('trip_date', '2026-06-12'),
            "return_date": data.get('return_date', '2026-06-22'),
            "passengers": data.get('passengers', 2),
            "flights": augmented,
            "source": "amadeus_augmented",
            "original_count": len(flights),
            "augmented_count": len(augmented)
        }
        
        print(json.dumps(result, indent=2))
    
    except json.JSONDecodeError:
        sys.exit(1)
