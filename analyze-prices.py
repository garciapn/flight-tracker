#!/usr/bin/env python3
"""
Flight Tracker - Price Analysis
Run after data collection to generate insights and update memory
"""
import json
import os
from datetime import datetime, timedelta
import re

BASE_DIR = "/Users/gerald/.openclaw/workspace/flight-tracker"
DATA_DIR = os.path.join(BASE_DIR, "data")
MEMORY_FILE = "/Users/gerald/.openclaw/workspace/MEMORY.md"

def load_latest_data():
    """Load the most recent flight data"""
    latest_file = None
    latest_date = None
    
    if os.path.exists(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR), reverse=True):
            if fname.endswith('.json') and re.match(r'\d{4}-\d{2}-\d{2}', fname.replace('.json', '')):
                latest_file = os.path.join(DATA_DIR, fname)
                latest_date = fname.replace('.json', '')
                break
    
    if latest_file:
        try:
            with open(latest_file) as f:
                return json.load(f), latest_date
        except:
            pass
    
    return None, None

def load_price_history():
    """Load all historical price data"""
    history = {}
    
    if os.path.exists(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR)):
            if fname.endswith('.json') and re.match(r'\d{4}-\d{2}-\d{2}', fname.replace('.json', '')):
                date_str = fname.replace('.json', '')
                try:
                    with open(os.path.join(DATA_DIR, fname)) as f:
                        data = json.load(f)
                        flights = data.get('flights', [])
                        if flights:
                            # Get cheapest flight for this date
                            cheapest = None
                            for flight in flights:
                                price_str = str(flight.get('price', '')).replace('$', '').replace(',', '')
                                try:
                                    price = float(price_str)
                                    if cheapest is None or price < cheapest['price']:
                                        cheapest = {'price': price, 'airline': flight.get('airline', 'Unknown')}
                                except:
                                    pass
                            
                            if cheapest:
                                history[date_str] = cheapest
                except:
                    pass
    
    return history

def analyze_prices():
    """Generate price insights"""
    data, today_date = load_latest_data()
    if not data:
        return None
    
    flights = data.get('flights', [])
    if not flights:
        return None
    
    # Extract prices
    prices = []
    for flight in flights[:5]:
        price_str = str(flight.get('price', '')).replace('$', '').replace(',', '')
        try:
            prices.append(float(price_str))
        except:
            pass
    
    if not prices:
        return None
    
    # Calculate stats
    cheapest = min(prices)
    most_expensive = max(prices)
    avg_price = sum(prices) / len(prices)
    
    # Load history for trend
    history = load_price_history()
    historical_prices = [v['price'] for v in history.values() if 'price' in v]
    
    trend = "stable"
    if historical_prices:
        avg_historical = sum(historical_prices) / len(historical_prices)
        if avg_price < avg_historical * 0.95:
            trend = "📉 dropping"
        elif avg_price > avg_historical * 1.05:
            trend = "📈 rising"
    
    # Days until trip
    trip_date = datetime(2026, 6, 12)
    days_until = (trip_date - datetime.now()).days
    
    return {
        'date': today_date,
        'cheapest': f"${cheapest:.0f}",
        'average': f"${avg_price:.0f}",
        'trend': trend,
        'days_until_trip': days_until,
        'top_carrier': flights[0].get('airline', 'Unknown'),
        'num_flights': len(flights)
    }

def update_memory(insights):
    """Update MEMORY.md with latest insights"""
    if not insights:
        return
    
    # Read current memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            content = f.read()
    else:
        content = ""
    
    # Find the pricing analysis section
    section_marker = "**Pricing Analysis"
    if section_marker in content:
        # Replace existing section
        parts = content.split(section_marker)
        before = parts[0]
        after_parts = parts[1].split('\n\n', 1)
        after = after_parts[1] if len(after_parts) > 1 else ""
        
        new_section = f"""**Pricing Analysis ({insights['date']}):**
- **Current:** {insights['average']}/person (cheapest: {insights['cheapest']})
- **Trend:** {insights['trend']}
- **Top carrier:** {insights['top_carrier']}
- **Days until trip:** {insights['days_until_trip']}
- **Data points:** {insights['num_flights']} flights tracked"""
        
        content = before + new_section + "\n\n" + after
    else:
        # Add new section after pricing section
        if "**Pricing Analysis" not in content:
            # Find Flight Tracker section and add after it
            marker = "## Project: Flight Tracker"
            if marker in content:
                parts = content.split(marker)
                new_section = f"""

**Pricing Analysis ({insights['date']}):**
- **Current:** {insights['average']}/person (cheapest: {insights['cheapest']})
- **Trend:** {insights['trend']}
- **Top carrier:** {insights['top_carrier']}
- **Days until trip:** {insights['days_until_trip']}
- **Data points:** {insights['num_flights']} flights tracked"""
                content = parts[0] + marker + parts[1] + new_section + ("\n" + parts[2] if len(parts) > 2 else "")
    
    # Write back
    try:
        with open(MEMORY_FILE, 'w') as f:
            f.write(content)
        print(f"✅ Updated MEMORY.md with price insights")
    except Exception as e:
        print(f"Failed to update memory: {e}")

if __name__ == "__main__":
    insights = analyze_prices()
    if insights:
        print(f"📊 Price Insights: Cheapest {insights['cheapest']}, Avg {insights['average']}, Trend {insights['trend']}")
        update_memory(insights)
    else:
        print("No price data to analyze")
