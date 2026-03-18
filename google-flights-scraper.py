#!/usr/bin/env python3
"""
Google Flights Playwright Scraper
Extracts real flight data from Google Flights with proper error handling and timeouts.
Supports parameterized routes and dates for reusability.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import re

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


class GoogleFlightsScraper:
    """Scrape Google Flights with Playwright"""
    
    def __init__(self, timeout_ms: int = 30000, headless: bool = True):
        """
        Initialize scraper with configurable timeouts
        
        Args:
            timeout_ms: Page load timeout in milliseconds
            headless: Run browser in headless mode
        """
        self.timeout_ms = timeout_ms
        self.headless = headless
        self.flights = []
        self.errors = []
    
    async def scrape(
        self, 
        origin: str = "SAN",
        destination: str = "ATH", 
        depart_date: str = "20260612",
        return_date: str = "20260622",
        passengers: int = 2,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Scrape Google Flights with retry logic
        
        Args:
            origin: Airport code (e.g., 'SAN')
            destination: Airport code (e.g., 'ATH')
            depart_date: YYYYMMDD format
            return_date: YYYYMMDD format
            passengers: Number of passengers
            max_retries: Max retry attempts on failure
        
        Returns:
            List of flight dictionaries sorted by price
        """
        url = f"https://www.google.com/flights?flt={origin}&to={destination}&depart_date={depart_date}&return_date={return_date}&passengers={passengers}"
        
        for attempt in range(max_retries):
            try:
                print(f"[Attempt {attempt + 1}/{max_retries}] Scraping: {origin} → {destination}")
                print(f"URL: {url}")
                return await self._scrape_page(url, origin, destination)
            except PlaywrightTimeoutError as e:
                self.errors.append({
                    "type": "timeout",
                    "attempt": attempt + 1,
                    "message": str(e)
                })
                print(f"  ⚠️  Timeout on attempt {attempt + 1}: {str(e)[:80]}")
                if attempt < max_retries - 1:
                    print(f"  ↻ Retrying in 3 seconds...")
                    await asyncio.sleep(3)
            except Exception as e:
                self.errors.append({
                    "type": "error",
                    "attempt": attempt + 1,
                    "message": str(e)
                })
                print(f"  ✗ Error on attempt {attempt + 1}: {str(e)[:80]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        
        print("✗ Failed to scrape after all retries")
        return []
    
    async def _scrape_page(self, url: str, origin: str, dest: str) -> List[Dict[str, Any]]:
        """Internal method to scrape the page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            page.set_default_timeout(self.timeout_ms)
            
            try:
                print(f"  → Loading page...")
                await page.goto(url, wait_until="domcontentloaded")
                
                # Wait for flight results to appear
                print(f"  → Waiting for flight results...")
                try:
                    await page.wait_for_selector("div[data-itinerary-id]", timeout=10000)
                except PlaywrightTimeoutError:
                    # Alternative selector
                    try:
                        await page.wait_for_selector("div.nrc6fd", timeout=5000)
                    except PlaywrightTimeoutError:
                        print("  ⚠️  No flight results found - page may be blocked or empty")
                        return []
                
                # Scroll to load more results
                print(f"  → Scrolling to load results...")
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(0.5)
                
                # Extract flight data
                print(f"  → Extracting flight data...")
                flights = await self._extract_flights(page)
                
                if flights:
                    print(f"  ✓ Found {len(flights)} flights")
                    return sorted(flights, key=lambda x: float(x.get("price", float("inf"))))
                else:
                    print(f"  ⚠️  No flights extracted from page")
                    return []
                
            finally:
                await browser.close()
    
    async def _extract_flights(self, page) -> List[Dict[str, Any]]:
        """Extract flight information from page"""
        flights = []
        
        # Try to get all flight result containers
        flight_containers = await page.query_selector_all(
            "div[data-itinerary-id], div.nrc6fd, div.UfBJHb"
        )
        
        if not flight_containers:
            print("  ⚠️  No flight containers found, trying alternative methods...")
            # Fallback: try to get text content and parse manually
            text = await page.text_content("body")
            if text and "$" in text:
                # Extract any prices mentioned
                prices = re.findall(r'\$(\d+)', text)
                if prices:
                    print(f"  📍 Found {len(set(prices))} unique prices in page text")
        
        for idx, container in enumerate(flight_containers[:50]):  # Limit to 50 results
            try:
                # Extract airline
                airline_elem = await container.query_selector("div.sSHqwe span")
                airline = await airline_elem.text_content() if airline_elem else "N/A"
                
                # Extract price
                price_elem = await container.query_selector("span.YMlIz.FpHyqf")
                if not price_elem:
                    price_elem = await container.query_selector("span[role='text']")
                
                price_text = await price_elem.text_content() if price_elem else None
                price = self._parse_price(price_text) if price_text else None
                
                if price is None:
                    continue
                
                # Extract times and duration
                time_elem = await container.query_selector("span.pIavsd")
                times_text = await time_elem.text_content() if time_elem else ""
                
                duration_elem = await container.query_selector("span.DYXfra")
                duration = await duration_elem.text_content() if duration_elem else "N/A"
                
                # Extract stops
                stops_elem = await container.query_selector("div.YxbF4e")
                stops_text = await stops_elem.text_content() if stops_elem else "1"
                stops = self._parse_stops(stops_text)
                
                # Extract layover info
                layovers = await self._extract_layovers(container)
                
                flight = {
                    "airline": airline.strip() if isinstance(airline, str) else "N/A",
                    "departure_time": self._parse_time(times_text, "departure"),
                    "arrival_time": self._parse_time(times_text, "arrival"),
                    "duration": duration.strip() if isinstance(duration, str) else "N/A",
                    "stops": stops,
                    "layovers": layovers,
                    "price": price,
                    "source": "google",
                    "booking_url": None
                }
                
                if price and stops is not None:
                    flights.append(flight)
                    print(f"    [{idx+1}] {airline} - ${price:.2f} ({stops} stops, {duration})")
                
            except Exception as e:
                self.errors.append({
                    "type": "extraction",
                    "index": idx,
                    "message": str(e)
                })
        
        return flights
    
    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """Parse price from text"""
        if not price_text:
            return None
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(cleaned) / 2  # Assuming Google shows per-person price, but let's capture raw
        except ValueError:
            return None
    
    @staticmethod
    def _parse_stops(stops_text: str) -> Optional[int]:
        """Parse number of stops"""
        if not stops_text:
            return None
        if "nonstop" in stops_text.lower():
            return 0
        match = re.search(r'(\d+)\s*stop', stops_text.lower())
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _parse_time(time_text: str, time_type: str) -> Optional[str]:
        """Parse departure/arrival time"""
        if not time_text:
            return None
        # Format: "6:10 PM – 2:20 PM + 1"
        times = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', time_text)
        if time_type == "departure" and times:
            return times[0]
        elif time_type == "arrival" and len(times) > 1:
            return times[1]
        return None
    
    async def _extract_layovers(self, container) -> List[Dict[str, str]]:
        """Extract layover information"""
        layovers = []
        try:
            layover_elems = await container.query_selector_all("div.EWp0qd")
            for elem in layover_elems[:3]:  # Max 3 layovers
                text = await elem.text_content()
                if text:
                    layovers.append({"info": text.strip()})
        except:
            pass
        return layovers


async def main():
    """Main entry point"""
    # Parse arguments
    origin = sys.argv[1] if len(sys.argv) > 1 else "SAN"
    destination = sys.argv[2] if len(sys.argv) > 2 else "ATH"
    depart = sys.argv[3] if len(sys.argv) > 3 else "20260612"
    return_dt = sys.argv[4] if len(sys.argv) > 4 else "20260622"
    pax = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    
    scraper = GoogleFlightsScraper(timeout_ms=45000, headless=True)
    
    flights = await scraper.scrape(
        origin=origin,
        destination=destination,
        depart_date=depart,
        return_date=return_dt,
        passengers=pax,
        max_retries=3
    )
    
    # Save results
    result = {
        "timestamp": datetime.now().isoformat(),
        "route": f"{origin}→{destination}",
        "dates": {
            "depart": depart,
            "return": return_dt
        },
        "passengers": pax,
        "flights_found": len(flights),
        "top_15": flights[:15],
        "errors": scraper.errors
    }
    
    output_file = Path("data/google-flights-latest.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    print(f"✓ Found {len(flights)} total flights, top 15 extracted")
    
    if flights:
        print(f"\nTop 5 cheapest flights:")
        for i, flight in enumerate(flights[:5], 1):
            print(f"  {i}. {flight['airline']:4s} - ${flight['price']:8.2f} ({flight['stops']} stops, {flight['duration']})")
    
    return flights


if __name__ == "__main__":
    asyncio.run(main())
