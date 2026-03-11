#!/usr/bin/env node
/**
 * Google Flights Scraper with Puppeteer
 * Actually renders JavaScript to get real flight data
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const BASE_DIR = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));

// Build Google Flights search URL
function buildGoogleFlightsUrl() {
  const { origin, destination, departDate, returnDate } = CONFIG.trip;
  
  // Google Flights URL format (outbound + return)
  const baseUrl = 'https://www.google.com/travel/flights';
  
  // Format: /search?tfs=CBwQAhokag...
  // Simplified approach: use the search endpoint with params
  return `${baseUrl}/search?tfs=CBwQAhokagcIARID${origin}EgoyMDI2LTA2LTEycgcIARID${destination}MgoIMhAAGAAiA1VTRAoIAhAAGAAiA1VTRABKAI`;
}

async function scrapeGoogleFlights() {
  console.log('🚀 Launching browser...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Set viewport and user agent
    await page.setViewport({ width: 1920, height: 1080 });
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36');
    
    const url = buildGoogleFlightsUrl();
    console.log(`📡 Loading: ${url.substring(0, 80)}...`);
    
    await page.goto(url, { 
      waitUntil: 'networkidle2',
      timeout: 60000 
    });
    
    // Wait for flight results to load
    console.log('⏳ Waiting for flight data...');
    await new Promise(resolve => setTimeout(resolve, 8000)); // Give it time to render
    
    // Take a screenshot for debugging
    const screenshotPath = path.join(BASE_DIR, 'data', 'screenshots', `${new Date().toISOString().split('T')[0]}.png`);
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`📸 Screenshot saved: ${screenshotPath}`);
    
    // Extract flight data
    const flightData = await page.evaluate(() => {
      const results = {
        prices: [],
        airlines: [],
        durations: [],
        stops: []
      };
      
      // Look for price elements (Google uses specific classes)
      document.querySelectorAll('[aria-label*="price"], [data-flt-ve="price"]').forEach(el => {
        const text = el.textContent;
        const priceMatch = text.match(/\$(\d{1,3}(?:,\d{3})*)/);
        if (priceMatch) {
          results.prices.push(parseInt(priceMatch[1].replace(/,/g, '')));
        }
      });
      
      // Extract any visible flight information
      const allText = document.body.innerText;
      const priceMatches = allText.match(/\$(\d{1,3}(?:,\d{3})*)/g);
      if (priceMatches) {
        priceMatches.forEach(match => {
          const price = parseInt(match.replace(/[$,]/g, ''));
          if (price > 200 && price < 5000) {
            results.prices.push(price);
          }
        });
      }
      
      return results;
    });
    
    console.log(`💰 Found ${flightData.prices.length} price references`);
    
    return flightData;
    
  } finally {
    await browser.close();
    console.log('✅ Browser closed');
  }
}

async function analyzeAndSave(rawData) {
  const prices = [...new Set(rawData.prices)].sort((a, b) => a - b);
  
  const data = {
    timestamp: new Date().toISOString(),
    route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
    departDate: CONFIG.trip.departDate,
    returnDate: CONFIG.trip.returnDate,
    passengers: CONFIG.trip.passengers,
    stats: {
      minPrice: prices[0] || null,
      maxPrice: prices[prices.length - 1] || null,
      avgPrice: prices.length ? Math.round(prices.reduce((a, b) => a + b) / prices.length) : null,
      medianPrice: prices[Math.floor(prices.length / 2)] || null,
      priceCount: prices.length
    },
    prices: prices.slice(0, 20), // Top 20 prices
    raw: rawData
  };
  
  // Save daily snapshot
  const today = new Date().toISOString().split('T')[0];
  const dataFile = path.join(BASE_DIR, 'data', `${today}.json`);
  fs.writeFileSync(dataFile, JSON.stringify(data, null, 2));
  
  // Append to history
  const historyFile = path.join(BASE_DIR, 'data', 'history.jsonl');
  fs.appendFileSync(historyFile, JSON.stringify(data) + '\n');
  
  console.log('\n📊 Results:');
  console.log(`   Min: $${data.stats.minPrice || 'N/A'}`);
  console.log(`   Avg: $${data.stats.avgPrice || 'N/A'}`);
  console.log(`   Max: $${data.stats.maxPrice || 'N/A'}`);
  console.log(`   Prices found: ${data.stats.priceCount}`);
  console.log(`\n💾 Saved to: ${dataFile}`);
  
  return data;
}

async function main() {
  console.log('🛫 Flight Tracker (Puppeteer) starting...\n');
  
  try {
    const rawData = await scrapeGoogleFlights();
    const results = await analyzeAndSave(rawData);
    
    console.log('\n✨ Done!');
    return results;
  } catch (err) {
    console.error('❌ Error:', err.message);
    throw err;
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { main, scrapeGoogleFlights };
