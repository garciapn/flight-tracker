# Next Steps - Flight Tracker Rebuild

## Immediate (Today - March 17)

### 1. Verify Amadeus Data Quality ✅
- [x] Run tracker: Got 50 real flights
- [x] Extract top 15: $2,973 - $3,404 range
- [x] Check structure: All fields present (airline, times, duration, stops)
- [x] Send to User: Telegram message with top 15

**Status:** COMPLETE ✅

### 2. Document All 3 Sources ✅
- [x] Amadeus: Working, documented
- [x] Google Flights: Blocked by JS rendering, documented
- [x] SerpAPI: Not configured, documented solution
- [x] Comparison matrix created
- [x] Recommendations documented

**Status:** COMPLETE ✅

---

## Short-term (This Week)

### 3. Enable Google Flights Scraping ⏳
**Priority:** HIGH (needed for price verification)

```bash
# Step 1: Install Playwright
pip install playwright
python3 -m playwright install chromium

# Step 2: Update unified-flight-scraper.py
# Add Playwright implementation to GoogleFlightsScraper class

# Step 3: Test
python3 unified-flight-scraper.py

# Expected: Should now show Google flights alongside Amadeus
```

**Code template:**
```python
from playwright.async_api import async_playwright

async def search_flights_playwright(self, depart, arrive, depart_date, return_date, passengers):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Build URL
        date_format = depart_date.replace('-', '')
        return_format = return_date.replace('-', '')
        url = f"https://www.google.com/flights?flt={depart}&to={arrive}&depart_date={date_format}&return_date={return_format}&passengers={passengers}"
        
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Extract flight data
        flights = await page.query_selector_all('.nHsCwe')  # Flight cards
        
        results = []
        for flight_elem in flights:
            price = await flight_elem.text_content()
            # Parse and extract fields...
        
        await browser.close()
        return results
```

### 4. Configure SerpAPI ⏳
**Priority:** HIGH (fallback/verification source)

```bash
# Step 1: Get free API key
# Visit: https://serpapi.com/
# Sign up for free tier (100 searches/month)
# Copy API key

# Step 2: Add to environment
echo 'export SERPAPI_KEY="your_api_key"' >> ~/.zshrc
source ~/.zshrc

# Step 3: Test
python3 -c "
import os
import requests
api_key = os.getenv('SERPAPI_KEY')
params = {
    'engine': 'google_flights',
    'departure_id': 'SAN',
    'arrival_id': 'ATH',
    'outbound_date': '2026-06-12',
    'return_date': '2026-06-22',
    'adults': 2,
    'api_key': api_key
}
r = requests.get('https://serpapi.com/search', params=params, timeout=10)
flights = r.json().get('best_flights', [])
print(f'Found {len(flights)} flights')
for f in flights[:3]:
    print(f'  {f[\"price\"]}: {f.get(\"flights\", [{}])[0].get(\"airline\")}')
"

# Step 4: Commit to .env
vim .env
# Add: SERPAPI_KEY="your_key"
```

---

## Medium-term (Week 2-3)

### 5. Set Up Daily Automation ⏳
**Priority:** HIGH (track price trends)

```bash
# Step 1: Create shell wrapper script
cat > run-unified-tracker.sh << 'EOF'
#!/bin/bash
set -e

cd /Users/gerald/.openclaw/workspace/flight-tracker

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Run tracker
python3 unified-flight-scraper.py >> logs/tracker.log 2>&1

# Archive results with timestamp
cp data/unified-results.json data/results-$(date +%Y%m%d-%H%M%S).json

echo "Flight tracker run complete: $(date)"
EOF

chmod +x run-unified-tracker.sh

# Step 2: Set up cron
crontab -e
# Add lines:
# 0 6 * * * cd /Users/gerald/.openclaw/workspace/flight-tracker && ./run-unified-tracker.sh
# 0 18 * * * cd /Users/gerald/.openclaw/workspace/flight-tracker && ./run-unified-tracker.sh

# Step 3: Verify cron
crontab -l
```

### 6. Add Price Drop Alerts ⏳
**Priority:** MEDIUM (notify when good deals appear)

```python
# In unified-flight-scraper.py, add after merging flights:

def check_price_alerts(flights, thresholds=[2500, 2300, 2200]):
    """Send alerts for price drops below threshold"""
    alerts = []
    
    for flight in flights:
        price = flight.price
        for threshold in thresholds:
            if price < threshold and flight.airline in ['Virgin Atlantic', 'United']:
                alerts.append({
                    'level': 'ALERT' if price < 2300 else 'INFO',
                    'price': price,
                    'airline': flight.airline,
                    'departure': flight.departure_time,
                    'threshold': threshold
                })
    
    return alerts

# Send alerts via Telegram
def send_price_alerts(alerts):
    for alert in alerts:
        message = f"""
🎉 PRICE DROP ALERT!
${alert['price']:.2f} - {alert['airline']}
Departure: {alert['departure']}
Below ${alert['threshold']} threshold
        """
        send_telegram(message)
```

---

## Long-term (Month 2+)

### 7. Build Comparison Dashboard ⏳
**Priority:** MEDIUM (visualize price trends)

```python
# Create dashboard showing:
# - Price trends over time (Amadeus vs Google vs SerpAPI)
# - Best deals highlighted
# - Airline comparison
# - Day-of-week pricing patterns
```

### 8. Historical Analysis & ML ⏳
**Priority:** LOW (advanced features)

```python
# Features to add:
# - Price prediction (when will prices drop further?)
# - Best booking windows (historically when is cheapest?)
# - Airline-specific patterns
# - Seasonal analysis
```

---

## Testing Checklist

- [ ] Amadeus returns 50+ flights ✅
- [ ] Top 15 extracted correctly ✅
- [ ] Prices in reasonable range ($2.9K - $3.4K) ✅
- [ ] All flights have required fields ✅
- [ ] JSON output is valid ✅
- [ ] Sent to Telegram ✅
- [ ] Google Flights scraping works (pending)
- [ ] SerpAPI integration works (pending)
- [ ] Cron runs without errors (pending)
- [ ] Alerts trigger correctly (pending)

---

## Troubleshooting

### "Amadeus authentication failed"
```bash
# Check credentials
echo $AMADEUS_CLIENT_ID
echo $AMADEUS_CLIENT_SECRET

# Verify in .env file
cat .env | grep AMADEUS

# Test directly
curl -X POST https://test.api.amadeus.com/v1/security/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$AMADEUS_CLIENT_ID&client_secret=$AMADEUS_CLIENT_SECRET"
```

### "ModuleNotFoundError: No module named 'playwright'"
```bash
# Install via pip in a virtual env (not system-wide)
python3 -m venv flight-env
source flight-env/bin/activate
pip install playwright
python3 -m playwright install
```

### "No flights found from Google"
```bash
# Google Flights is JS-rendered, raw HTML won't work
# Must use Playwright headless browser (see Step 3 above)
# Or use SerpAPI as workaround
```

### "SerpAPI rate limit exceeded"
```bash
# Free tier is 100 searches/month
# Check usage at https://serpapi.com/dashboard
# Options:
# 1. Reduce frequency (once daily instead of twice)
# 2. Upgrade to paid plan ($10-50/month)
# 3. Use Amadeus only (no API limits)
```

---

## Timeline

**Week of March 17 (NOW)**
- [x] Rebuild tracker with Amadeus ✅
- [x] Document all 3 sources ✅
- [ ] Test Google Flights scraping
- [ ] Get SerpAPI key

**Week of March 24**
- [ ] Enable Google + SerpAPI
- [ ] Set up daily cron runs
- [ ] Add price alerts

**Week of March 31**
- [ ] Historical trend analysis
- [ ] Dashboard (basic)
- [ ] Fine-tune alert thresholds

**April+**
- [ ] ML price prediction
- [ ] Multi-route support
- [ ] Advanced features

---

## Resources

- **Amadeus API Docs:** https://developers.amadeus.com/
- **Playwright Docs:** https://playwright.dev/python/
- **SerpAPI Flights:** https://serpapi.com/docs/flights_api
- **Google Flights:** https://www.google.com/flights

---

**Current Status:** ✅ Phase 1 (data collection) COMPLETE
**Next Phase:** Phase 2 (verification & automation)
