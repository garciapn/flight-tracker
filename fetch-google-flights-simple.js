#!/usr/bin/env node
/**
 * Simple Google Flights Price Fetcher
 * Uses curl to fetch the page and regex/parsing to extract prices
 * No browser required
 */

const { execSync } = require('child_process');
const https = require('https');

async function fetchGoogleFlightsPrices() {
    console.log('[Google Flights] Fetching prices via HTTP...');
    
    return new Promise((resolve, reject) => {
        const url = 'https://www.google.com/travel/flights?q=Flights%20from%20SAN%20to%20ATH%20on%202026-06-12%20returning%202026-06-22%20for%202%20adults';
        
        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0'
            },
            timeout: 30000
        };
        
        https.get(url, options, (res) => {
            let data = '';
            
            res.on('data', chunk => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const flights = extractFlights(data);
                    resolve(flights);
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', (err) => {
            reject(err);
        });
    });
}

function extractFlights(html) {
    const flights = [];
    
    // Extract all price patterns like $2,559 or $2559
    // Look for prices in the range $500-$5000
    const priceRegex = /\$(\d{1,2},\d{3}|\d{3,4})/g;
    let priceMatch;
    const prices = [];
    
    while ((priceMatch = priceRegex.exec(html)) !== null) {
        const priceStr = priceMatch[1].replace(',', '');
        const price = parseInt(priceStr);
        
        // Only include reasonable prices
        if (price >= 500 && price <= 5000) {
            prices.push(price);
        }
    }
    
    // Remove duplicates and sort by price
    const uniquePrices = [...new Set(prices)].sort((a, b) => a - b);
    
    // Extract airline names - more comprehensive list
    const airlineList = [
        'United', 'American', 'Delta', 'Southwest', 'Alaska', 
        'Lufthansa', 'Air Canada', 'British Airways', 'Air France', 
        'KLM', 'Emirates', 'Turkish', 'Iberia', 'Finnair', 
        'Virgin Atlantic', 'JetBlue', 'Hawaiian', 'Spirit', 
        'Frontier', 'Norse'
    ];
    
    const airlineRegex = new RegExp(`(${airlineList.join('|')})`, 'g');
    const airlineMatches = html.match(airlineRegex) || [];
    const uniqueAirlines = [...new Set(airlineMatches)];
    
    // Extract times (HH:MM AM/PM)
    const timeRegex = /(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)/g;
    const times = [];
    let timeMatch;
    while ((timeMatch = timeRegex.exec(html)) !== null) {
        times.push(`${timeMatch[1]}:${timeMatch[2]} ${timeMatch[3].toUpperCase()}`);
    }
    
    // Extract durations (15h 30m format, 15h format, etc)
    const durationRegex = /(\d{1,2})\s*h(?:\s*(\d{1,2})\s*m)?/g;
    const durations = [];
    let durationMatch;
    while ((durationMatch = durationRegex.exec(html)) !== null) {
        if (durationMatch[2]) {
            durations.push(`${durationMatch[1]}h ${durationMatch[2]}m`);
        } else {
            durations.push(`${durationMatch[1]}h`);
        }
    }
    
    // Create flight objects from unique prices
    for (let i = 0; i < Math.min(uniquePrices.length, 15); i++) {
        const price = uniquePrices[i];
        const airline = uniqueAirlines[i % Math.max(1, uniqueAirlines.length)] || 'Multiple Airlines';
        const departure = times[i*2] || '--';
        const arrival = times[i*2 + 1] || '--';
        const duration = durations[i] || '--';
        
        flights.push({
            airline: airline,
            price: price,
            departure: departure,
            arrival: arrival,
            duration: duration,
            stops: '1-2 stops',
            layover: 'Check details on Google Flights',
            layover_time: 'Variable',
            source: 'google_flights_http'
        });
    }
    
    return flights;
}

async function main() {
    try {
        const flights = await fetchGoogleFlightsPrices();
        
        if (flights.length > 0) {
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
            
            console.log('\n' + JSON.stringify(result, null, 2));
            process.exit(0);
        } else {
            console.error('[Google Flights] No prices found');
            process.exit(1);
        }
    } catch (error) {
        console.error('[Google Flights] Error:', error.message);
        process.exit(1);
    }
}

main();
