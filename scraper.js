#!/usr/bin/env node
/**
 * Google Flights Scraper for SAN → ATH
 * Fetches public flight data without API keys
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BASE_DIR = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));

// Build Google Flights URL
function buildGoogleFlightsUrl(origin, dest, date, returnDate = null) {
  const baseUrl = 'https://www.google.com/travel/flights';
  
  // Google Flights URL format
  const params = new URLSearchParams({
    tfs: `f.0.t.${origin}.${dest}.${date}` + (returnDate ? `.1.t.${dest}.${origin}.${returnDate}` : '')
  });
  
  return `${baseUrl}?${params.toString()}`;
}

// Scrape using curl (basic, can upgrade to puppeteer later)
async function fetchFlightPage() {
  const url = buildGoogleFlightsUrl(
    CONFIG.trip.origin,
    CONFIG.trip.destination,
    CONFIG.trip.departDate,
    CONFIG.trip.returnDate
  );
  
  console.log(`📡 Fetching: ${url}`);
  
  try {
    // Use curl to fetch the page
    const html = execSync(`curl -s "${url}"`, { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
    
    // Save raw HTML for inspection
    const today = new Date().toISOString().split('T')[0];
    const rawDir = path.join(BASE_DIR, 'data', 'raw');
    if (!fs.existsSync(rawDir)) fs.mkdirSync(rawDir, { recursive: true });
    
    fs.writeFileSync(
      path.join(rawDir, `${today}-${Date.now()}.html`),
      html
    );
    
    return html;
  } catch (err) {
    console.error('❌ Fetch failed:', err.message);
    return null;
  }
}

// Parse flight data from HTML (basic regex parsing)
function parseFlights(html) {
  // Google Flights embeds data in JSON-LD or script tags
  // This is a simplified parser - we'll refine it
  
  const flights = [];
  
  // Look for price patterns (e.g., "$850", "€750")
  const priceMatches = html.match(/\$[\d,]+|\€[\d,]+/g);
  
  if (priceMatches) {
    console.log(`💰 Found ${priceMatches.length} price references`);
    flights.push({
      timestamp: new Date().toISOString(),
      prices: priceMatches.slice(0, 10), // Top 10
      source: 'google_flights',
      route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
      date: CONFIG.trip.departDate
    });
  }
  
  return flights;
}

async function main() {
  console.log('🛫 Google Flights Scraper starting...');
  
  const html = await fetchFlightPage();
  if (!html) {
    console.log('⚠️  No data fetched');
    return;
  }
  
  const flights = parseFlights(html);
  
  // Save parsed data
  const today = new Date().toISOString().split('T')[0];
  const dataFile = path.join(BASE_DIR, 'data', `${today}.json`);
  
  fs.writeFileSync(dataFile, JSON.stringify({
    timestamp: new Date().toISOString(),
    flights,
    meta: {
      source: 'google_flights_scraper',
      trip: CONFIG.trip
    }
  }, null, 2));
  
  console.log(`✅ Saved to ${dataFile}`);
  console.log(`📊 Parsed ${flights.length} flight entries`);
}

main().catch(console.error);
