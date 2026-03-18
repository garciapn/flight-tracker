#!/usr/bin/env python3
"""
Unified Flight Aggregator - PHASE 3
Combines data from Amadeus, Google Flights, and SerpAPI.
Deduplicates, ranks by price + quality, returns top 15.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple


class FlightAggregator:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def aggregate(
        self,
        google_flights_file: str = "google-flights-results.json",
        serpapi_file: str = "serpapi-results.json",
        amadeus_file: str = "amadeus-results.json"
    ) -> dict:
        """Aggregate flights from all sources."""
        
        print("🔄 Aggregating flights from all sources...")
        
        all_flights = []
        sources_used = []
        
        # Load Google Flights
        google_flights = self._load_source(google_flights_file)
        if google_flights:
            sources_used.append(google_flights["source"])
            all_flights.extend(google_flights.get("flights", []))
            print(f"✅ Loaded {len(google_flights.get('flights', []))} from Google Flights")
        
        # Load SerpAPI
        serpapi_results = self._load_source(serpapi_file)
        if serpapi_results:
            sources_used.append(serpapi_results["source"])
            all_flights.extend(serpapi_results.get("flights", []))
            print(f"✅ Loaded {len(serpapi_results.get('flights', []))} from SerpAPI")
        
        # Load Amadeus
        amadeus_results = self._load_source(amadeus_file)
        if amadeus_results:
            sources_used.append(amadeus_results["source"])
            all_flights.extend(amadeus_results.get("flights", []))
            print(f"✅ Loaded {len(amadeus_results.get('flights', []))} from Amadeus")
        
        print(f"\n📊 Total flights before dedup: {len(all_flights)}")
        
        # Deduplicate
        unique_flights = self._deduplicate(all_flights)
        print(f"📊 Total flights after dedup: {len(unique_flights)}")
        
        # Score and rank
        scored_flights = self._score_flights(unique_flights)
        ranked_flights = sorted(scored_flights, key=lambda x: x["score"], reverse=True)
        
        # Get top 15
        top_15 = ranked_flights[:15]
        
        # Re-rank by price for final output
        top_15_by_price = sorted(top_15, key=lambda x: x["price"])
        
        # Add final ranks
        for idx, flight in enumerate(top_15_by_price):
            flight["rank"] = idx + 1
        
        # Calculate stats
        stats = self._calculate_stats(top_15_by_price)
        
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sources": sources_used,
            "aggregation_stats": {
                "total_flights_processed": len(all_flights),
                "unique_flights": len(unique_flights),
                "top_flights_returned": len(top_15_by_price)
            },
            "stats": stats,
            "flights": top_15_by_price
        }
        
        return result
    
    def _load_source(self, filename: str) -> dict:
        """Load results from a single source."""
        
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  {filename} not found")
            return None
        
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return None
    
    def _deduplicate(self, flights: List[dict]) -> List[dict]:
        """Remove duplicate flights (same airline + times)."""
        
        seen = {}
        unique = []
        
        for flight in flights:
            # Create a key based on airline, departure, and arrival
            key = (
                flight.get("airline", "").lower(),
                flight.get("departure", ""),
                flight.get("arrival", "")
            )
            
            if key not in seen:
                seen[key] = flight
                unique.append(flight)
            else:
                # Keep the cheaper option
                if flight.get("price", float("inf")) < seen[key].get("price", float("inf")):
                    # Replace with cheaper option
                    unique.remove(seen[key])
                    seen[key] = flight
                    unique.append(flight)
        
        return unique
    
    def _score_flights(self, flights: List[dict]) -> List[dict]:
        """Score flights based on price + quality metrics."""
        
        # Normalize prices to 0-100 scale
        if not flights:
            return flights
        
        prices = [f.get("price", 0) for f in flights]
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price if max_price > min_price else 1
        
        scored = []
        
        for flight in flights:
            price = flight.get("price", 0)
            duration_str = flight.get("duration", "24h")
            stops_str = flight.get("stops", "2 stops")
            
            # Parse duration to hours
            duration_hours = self._parse_duration(duration_str)
            
            # Parse stops
            stops = self._parse_stops(stops_str)
            
            # Price score (lower is better: 0-50 points)
            price_score = 50 - ((price - min_price) / price_range * 50)
            
            # Duration score (lower is better: 0-30 points)
            # Target: 14 hours is perfect, deduct for longer
            duration_score = max(0, 30 - (duration_hours - 14) * 2)
            
            # Stops score (fewer is better: 0-20 points)
            stops_score = max(0, 20 - (stops * 10))
            
            # Total score
            total_score = price_score + duration_score + stops_score
            
            flight["score"] = round(total_score, 2)
            flight["duration_hours"] = duration_hours
            flight["stops_count"] = stops
            
            scored.append(flight)
        
        return scored
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to hours."""
        
        try:
            parts = duration_str.split()
            hours = 0
            mins = 0
            
            for i, part in enumerate(parts):
                if 'h' in part:
                    hours = int(part.replace('h', ''))
                elif 'm' in part:
                    mins = int(part.replace('m', ''))
            
            return hours + (mins / 60)
        except:
            return 24.0
    
    def _parse_stops(self, stops_str: str) -> int:
        """Parse stops string to count."""
        
        try:
            # Extract number from "X stops" or "X stop"
            import re
            match = re.search(r'(\d+)', stops_str)
            if match:
                return int(match.group(1))
            elif "direct" in stops_str.lower():
                return 0
            else:
                return 2
        except:
            return 2
    
    def _calculate_stats(self, flights: List[dict]) -> dict:
        """Calculate price statistics."""
        
        if not flights:
            return {}
        
        prices = [f.get("price", 0) for f in flights]
        
        prices_sorted = sorted(prices)
        n = len(prices_sorted)
        
        if n == 1:
            median = prices_sorted[0]
        elif n % 2 == 0:
            median = (prices_sorted[n//2 - 1] + prices_sorted[n//2]) / 2
        else:
            median = prices_sorted[n//2]
        
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Recommended budget is average + 5% buffer
        recommended_budget = int(avg_price * 1.05)
        
        return {
            "total_flights": len(flights),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": round(avg_price, 2),
            "median_price": round(median, 2),
            "recommended_budget": recommended_budget,
            "price_range": max(prices) - min(prices)
        }
    
    def save_results(self, results: dict, filename: str = "aggregated-flights.json"):
        """Save aggregated results."""
        
        output_path = self.data_dir / filename
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Saved aggregated results: {output_path}")
        return output_path


def display_results(results: dict):
    """Display results in human-readable format."""
    
    print("\n" + "="*70)
    print("✈️ UNIFIED FLIGHT AGGREGATION RESULTS")
    print("="*70)
    
    print(f"\n📊 Sources: {', '.join(results.get('sources', []))}")
    
    stats = results.get("aggregation_stats", {})
    print(f"\n📈 Aggregation Stats:")
    print(f"   • Flights processed: {stats.get('total_flights_processed')}")
    print(f"   • Unique flights: {stats.get('unique_flights')}")
    print(f"   • Top flights returned: {stats.get('top_flights_returned')}")
    
    price_stats = results.get("stats", {})
    print(f"\n💰 Price Statistics:")
    print(f"   • Minimum: ${price_stats.get('min_price')}")
    print(f"   • Maximum: ${price_stats.get('max_price')}")
    print(f"   • Average: ${price_stats.get('avg_price')}")
    print(f"   • Median: ${price_stats.get('median_price')}")
    print(f"   • Recommended budget: ${price_stats.get('recommended_budget')}")
    
    flights = results.get("flights", [])
    print(f"\n🏆 TOP 15 FLIGHTS (Ranked by Price):")
    print("-" * 70)
    
    for flight in flights[:15]:
        print(f"\n#{flight.get('rank')}. ${flight.get('price')} (${flight.get('price_per_person')}/person)")
        print(f"    ✈️  {flight.get('airline')} | {flight.get('duration')} | {flight.get('stops')}")
        print(f"    🕐 {flight.get('departure')} → {flight.get('arrival')}")
        print(f"    📊 Score: {flight.get('score', 'N/A')}")


def main():
    """Main entry point."""
    
    aggregator = FlightAggregator()
    
    results = aggregator.aggregate()
    
    # Display
    display_results(results)
    
    # Save
    aggregator.save_results(results)
    
    return results


if __name__ == "__main__":
    main()
