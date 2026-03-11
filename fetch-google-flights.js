#!/usr/bin/env node
/**
 * Google Flights Real-Time Price Fetcher
 * Uses Puppeteer to scrape actual prices from Google Flights
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const TIMEOUT = 30000;
const BASE_DIR = __dirname;

function findChromium() {
    // Try to find chromium executable
    try {
        // macOS paths
        const paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome'
        ];
        
        for (const p of paths) {
            try {
                execSync(`test -x "${p}"`, { stdio: 'ignore' });
                console.log(`[Google Flights] Found Chrome at: ${p}`);
                return p;
            } catch (e) {
                continue;
            }
        }
        
        // Try which command
        try {
            const result = execSync('which google-chrome 2>/dev/null || which chromium 2>/dev/null', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
            if (result) {
                console.log(`[Google Flights] Found Chrome via which: ${result}`);
                return result;
            }
        } catch (e) {
            // continue
        }
    } catch (e) {
        // continue
    }
    
    return null;
}

async function fetchGoogleFlights() {
    console.log('[Google Flights] Starting real price fetch...');
    
    let browser = null;
    try {
        const executablePath = findChromium();
        
        if (!executablePath) {
            console.error('[Google Flights] Error: Chrome/Chromium not found');
            console.error('[Google Flights] Please install Google Chrome or Chromium');
            throw new Error('Chrome executable not found');
        }
        
        // Launch browser
        browser = await puppeteer.launch({
            headless: true,
            executablePath: executablePath,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        const page = await browser.newPage();
        const url = 'https://www.google.com/travel/flights?q=Flights%20from%20SAN%20to%20ATH%20on%202026-06-12%20returning%202026-06-22%20for%202%20adults';
        
        console.log('[Google Flights] Loading page...');
        await page.goto(url, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        
        // Wait for flight cards to load
        await page.waitForSelector('[data-test-id="multiway-options-list"]', { timeout: 10000 }).catch(() => null);
        
        // Extract flight data using page evaluation
        const flights = await page.evaluate(() => {
            const flightCards = [];
            const cards = document.querySelectorAll('[data-test-id="flight-card"]');
            
            cards.forEach((card, idx) => {
                if (idx >= 15) return; // Limit to 15 flights
                
                try {
                    // Extract price
                    const priceElem = card.querySelector('[data-is-best-price], [aria-label*="$"]');
                    const priceText = priceElem?.textContent || priceElem?.getAttribute('aria-label') || '';
                    const priceMatch = priceText.match(/\$[\d,]+/);
                    const price = priceMatch ? priceMatch[0].replace('$', '').replace(',', '') : null;
                    
                    if (!price) return;
                    
                    // Extract airline(s)
                    const airlineElems = card.querySelectorAll('[data-test-id="airline-badge"], [aria-label*="airline"]');
                    const airlines = Array.from(airlineElems)
                        .map(el => el.textContent?.trim() || el.getAttribute('aria-label'))
                        .filter(Boolean)
                        .slice(0, 2)
                        .join(' + ') || 'Multiple Airlines';
                    
                    // Extract times
                    const timeElems = card.querySelectorAll('[data-test-id="departure-time"], [data-test-id="arrival-time"]');
                    const times = Array.from(timeElems).map(el => el.textContent?.trim()).filter(Boolean);
                    const departure = times[0] || '--';
                    const arrival = times[1] || '--';
                    
                    // Extract duration
                    const durationElem = card.querySelector('[data-test-id="total-duration"]');
                    const duration = durationElem?.textContent?.trim() || 'N/A';
                    
                    // Extract stops
                    const stopsElem = card.querySelector('[data-test-id="flight-stops"]');
                    const stops = stopsElem?.textContent?.trim() || '1 stop';
                    
                    flightCards.push({
                        airline: airlines,
                        price: parseInt(price),
                        departure: departure,
                        arrival: arrival,
                        duration: duration,
                        stops: stops,
                        layover: 'See details',
                        layover_time: 'See details',
                        source: 'google_flights'
                    });
                } catch (e) {
                    console.warn('Failed to parse flight card:', e.message);
                }
            });
            
            return flightCards;
        });
        
        if (flights.length === 0) {
            console.log('[Google Flights] No flights found, trying alternate selectors...');
            
            // Try alternate scraping method
            const altFlights = await page.evaluate(() => {
                const results = [];
                const allText = document.body.innerText;
                
                // Look for price patterns in visible text
                const priceRegex = /\$(\d{3,4}(?:,\d{3})?)/g;
                const matches = [...allText.matchAll(priceRegex)];
                
                matches.slice(0, 10).forEach((match, idx) => {
                    results.push({
                        airline: 'Google Flights Option ' + (idx + 1),
                        price: parseInt(match[1].replace(',', '')),
                        departure: '--',
                        arrival: '--',
                        duration: 'Check details',
                        stops: '1-2 stops',
                        layover: 'Variable',
                        layover_time: 'Variable',
                        source: 'google_flights'
                    });
                });
                
                return results;
            });
            
            if (altFlights.length > 0) {
                console.log(`[Google Flights] Found ${altFlights.length} flights via alternate method`);
                await browser.close();
                return altFlights;
            }
        }
        
        console.log(`[Google Flights] ✅ Fetched ${flights.length} real Google Flights prices`);
        await browser.close();
        return flights;
        
    } catch (error) {
        console.error('[Google Flights] Error:', error.message);
        if (browser) await browser.close();
        return null;
    }
}

async function main() {
    const flights = await fetchGoogleFlights();
    
    if (flights && flights.length > 0) {
        const result = {
            timestamp: new Date().toISOString(),
            route: 'SAN→ATH',
            trip_date: '2026-06-12',
            return_date: '2026-06-22',
            passengers: 2,
            flights: flights,
            source: 'google_flights_live',
            count: flights.length
        };
        
        console.log(JSON.stringify(result, null, 2));
        process.exit(0);
    } else {
        console.error('[Google Flights] Failed to fetch prices');
        process.exit(1);
    }
}

main();
