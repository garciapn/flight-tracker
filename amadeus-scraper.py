#!/usr/bin/env python3
"""
Amadeus API Flight Scraper
Real-time flight data from Amadeus API (250+ options per search)
Replaces Google Flights scraping with official API
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AmadeusFlightScraper:
    """Amadeus API flight scraper"""
    
    # Airline code to full name mapping
    AIRLINE_NAMES = {
        'UA': 'United',
        'AA': 'American',
        'DL': 'Delta',
        'SW': 'Southwest',
        'AS': 'Alaska',
        'LH': 'Lufthansa',
        'BA': 'British Airways',
        'AF': 'Air France',
        'KL': 'KLM',
        'AC': 'Air Canada',
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'TK': 'Turkish Airlines',
        'IB': 'Iberia',
        'AY': 'Finnair',
        'VS': 'Virgin Atlantic',
        'B6': 'JetBlue',
        'NH': 'ANA',
        'SQ': 'Singapore Airlines',
        'CX': 'Cathay Pacific',
        'AZ': 'Alitalia',
        'OS': 'Austrian',
        'LX': 'Swiss',
        'SK': 'SAS',
        'TP': 'TAP Portugal',
        'RJ': 'Royal Jordanian',
        'SU': 'Aeroflot',
        'OK': 'Czech Airlines',
        'JL': 'Japan Airlines',
        'UA': 'United',
        'UN': 'United',
    }
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://test.api.amadeus.com"
    
    def authenticate(self) -> bool:
        """Get OAuth2 access token from Amadeus"""
        try:
            auth_url = f"{self.base_url}/v1/security/oauth2/token"
            auth_data = f"grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}"
            
            cmd = [
                "curl", "-s", "-X", "POST",
                auth_url,
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", auth_data
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                token_data = json.loads(result.stdout)
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 1800)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                print(f"✅ Amadeus authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {result.returncode}")
                print(f"   {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """Check if access token is still valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        adults: int = 2
    ) -> Optional[List[Dict]]:
        """
        Search for round-trip flights
        
        Args:
            origin: IATA code (e.g., 'SAN')
            destination: IATA code (e.g., 'ATH')
            departure_date: ISO date format (e.g., '2026-06-12')
            return_date: ISO date format (e.g., '2026-06-22')
            adults: Number of adult passengers
        
        Returns:
            List of flight offers or None
        """
        # Re-authenticate if needed
        if not self.is_token_valid():
            if not self.authenticate():
                return None
        
        try:
            flight_url = f"{self.base_url}/v2/shopping/flight-offers"
            
            query_string = f"originLocationCode={origin}&destinationLocationCode={destination}&departureDate={departure_date}&returnDate={return_date}&adults={adults}"
            
            print(f"🔍 Searching: {origin} → {destination}, {departure_date} to {return_date}, {adults} passengers")
            
            cmd = [
                "curl", "-s",
                f"{flight_url}?{query_string}",
                "-H", f"Authorization: Bearer {self.access_token}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                if "errors" in data:
                    print(f"❌ Search failed: {data['errors'][0].get('detail', 'Unknown error')}")
                    return None
                
                flights = data.get('data', [])
                print(f"✅ Found {len(flights)} flight combinations")
                return flights
            else:
                print(f"❌ Search failed: {result.returncode}")
                print(f"   {result.stderr[:200]}")
                return None
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    def format_flights_for_dashboard(self, flights: List[Dict]) -> List[Dict]:
        """
        Convert Amadeus flight offers to dashboard format
        
        Sorts by price (cheapest first) and extracts key info
        """
        formatted = []
        
        for flight in flights:
            try:
                price_info = flight.get('price', {})
                total_price = float(price_info.get('total', 0))
                per_person_price = total_price / 2  # For 2 passengers
                
                itineraries = flight.get('itineraries', [])
                if len(itineraries) < 2:
                    continue  # Skip one-way flights
                
                # Outbound leg
                outbound = itineraries[0]
                out_segments = outbound.get('segments', [])
                if not out_segments:
                    continue
                
                out_dep = out_segments[0].get('departure', {})
                out_arr = out_segments[-1].get('arrival', {})
                out_duration = outbound.get('duration', 'N/A')
                out_airlines = [s.get('operating', {}).get('carrierCode', s.get('carrierCode')) 
                               for s in out_segments]
                
                # Return leg
                ret_departure_date = None
                ret_airlines = []
                
                if len(itineraries) > 1:
                    ret_leg = itineraries[1]
                    ret_segments = ret_leg.get('segments', [])
                    if ret_segments:
                        ret_dep = ret_segments[0].get('departure', {})
                        ret_departure_date = ret_dep.get('at', '')
                        ret_airlines = [s.get('operating', {}).get('carrierCode', s.get('carrierCode')) 
                                       for s in ret_segments]
                
                # Parse times
                out_dep_time = out_dep.get('at', '')
                out_arr_time = out_arr.get('at', '')
                
                # Format departure/arrival for display
                if out_dep_time:
                    out_dep_display = out_dep_time[11:16]  # HH:MM
                else:
                    out_dep_display = "--"
                
                if out_arr_time:
                    # Check for next-day arrival (indicated by +1, +2 in time)
                    arr_hour = int(out_arr_time[11:13])
                    dep_hour = int(out_dep_time[11:13])
                    
                    # Simple heuristic: if arrival hour < departure hour, likely next day
                    next_day_indicator = ""
                    if arr_hour < dep_hour:
                        next_day_indicator = "+1"
                    
                    out_arr_display = f"{out_arr_time[11:16]}{next_day_indicator}"
                else:
                    out_arr_display = "--"
                
                # Convert duration PT format to readable format
                duration_readable = self._parse_duration(out_duration)
                
                # Build formatted flight
                formatted_flight = {
                    "airline": " + ".join([self._get_airline_name(code) for code in out_airlines]),
                    "departure": out_dep_display,
                    "arrival": out_arr_display,
                    "price": f"${per_person_price:.0f}",
                    "duration": duration_readable,
                    "stops": f"{len(out_segments) - 1} stop{'s' if len(out_segments) > 2 else ''}",
                    "layover": self._get_layover_info(out_segments),
                    "layover_time": self._get_layover_duration(out_segments),
                    "booking_url": self._get_booking_url(flight),
                    "amadeus_id": flight.get('id'),
                    "raw_price": total_price,
                    "raw_price_per_person": per_person_price
                }
                
                formatted.append(formatted_flight)
            except Exception as e:
                print(f"⚠️  Error formatting flight: {e}")
                continue
        
        # Sort by price (cheapest first)
        formatted.sort(key=lambda x: x.get('raw_price_per_person', float('inf')))
        
        return formatted[:10]  # Return top 10 cheapest
    
    def _get_airline_name(self, code: str) -> str:
        """Convert airline code to full name"""
        return self.AIRLINE_NAMES.get(code.upper(), code.upper())
    
    def _parse_duration(self, iso_duration: str) -> str:
        """Convert PT format (e.g., PT15H20M) to readable format"""
        if not iso_duration or not iso_duration.startswith('PT'):
            return iso_duration
        
        duration = iso_duration[2:]  # Remove 'PT'
        hours = 0
        minutes = 0
        
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
    
    def _get_layover_info(self, segments: List[Dict]) -> str:
        """Extract layover information from segments"""
        if len(segments) < 2:
            return "Direct"
        
        # Get the layover airport (arrival of first segment = departure of second)
        layover_airport = segments[0].get('arrival', {}).get('iataCode', '?')
        
        # Calculate layover duration
        arr_time = segments[0].get('arrival', {}).get('at', '')
        dep_time = segments[1].get('departure', {}).get('at', '')
        
        if arr_time and dep_time:
            # Parse times and calculate duration
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
    
    def _get_layover_duration(self, segments: List[Dict]) -> str:
        """Get just the layover duration (for price history modal)"""
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
    
    def _get_booking_url(self, flight: Dict) -> str:
        """Generate booking URL for the flight"""
        # For now, link to Amadeus flight offer
        # In production, would generate proper booking link
        amadeus_id = flight.get('id', '')
        return f"https://www.amadeus.com/flight-booking/{amadeus_id}"


def main():
    """Main function for testing"""
    # Get credentials from environment
    client_id = os.getenv('AMADEUS_CLIENT_ID')
    client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET")
        return
    
    # Create scraper
    scraper = AmadeusFlightScraper(client_id, client_secret)
    
    # Search flights
    flights = scraper.search_flights(
        origin="SAN",
        destination="ATH",
        departure_date="2026-06-12",
        return_date="2026-06-22",
        adults=2
    )
    
    if flights:
        formatted = scraper.format_flights_for_dashboard(flights)
        
        print("\n" + "=" * 80)
        print("TOP 5 FLIGHTS (formatted for dashboard)")
        print("=" * 80 + "\n")
        
        for i, flight in enumerate(formatted[:5], 1):
            print(f"{i}. {flight['airline']}")
            print(f"   Price: {flight['price']} per person")
            print(f"   {flight['departure']} → {flight['arrival']} ({flight['duration']})")
            print(f"   {flight['stops']} | {flight['layover']}")
            print()


if __name__ == "__main__":
    main()
