#!/usr/bin/env node
/**
 * Google Flights Scraper - Final Version
 * Uses direct search URL that actually works
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const BASE_DIR = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));

// Build proper Google Flights URL
function buildSearchUrl() {
  const { origin, destination, departDate, returnDate } = CONFIG.trip;
  
  // Format dates as YYYY-MM-DD
  const outDate = departDate.replace(/-/g, '-');
  const retDate = returnDate.replace(/-/g, '-');
  
  // Build the URL manually - this format definitely works
  return `https://www.google.com/travel/flights?q=Flights%20to%20${destination}%20from%20${origin}%20on%20${outDate}%20through%20${retDate}%20for%202%20adults`;
}

async function scrapeFlights() {
  console.log('🚀 Launching browser...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled'
    ]
  });
  
  try {
    const page = await browser.newPage();
    
    // Set realistic viewport and user agent
    await page.setViewport({ width: 1920, height: 1080 });
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    
    const url = buildSearchUrl();
    console.log(`📡 Loading Google Flights...`);
    console.log(`   ${url.substring(0, 100)}...`);
    
    // Navigate and wait for content
    await page.goto(url, { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 
    });
    
    console.log('⏳ Waiting for results to render...');
    await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10s for JS to render
    
    // Extract ALL text content first
    const pageText = await page.evaluate(() => document.body.innerText);
    
    // Save raw text for analysis
    fs.writeFileSync(
      path.join(BASE_DIR, 'data', 'page-text-latest.txt'),
      pageText
    );
    
    // Save screenshot (with error handling)
    try {
      const screenshotPath = path.join(BASE_DIR, 'data', 'screenshots', `latest.png`);
      fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`📸 Screenshot: ${screenshotPath}`);
    } catch (screenshotErr) {
      console.log(`⚠️ Screenshot skipped (${screenshotErr.message})`);
    }
    
    // Parse prices from text
    const priceMatches = pageText.match(/\$\s*(\d{1,3}(?:,\d{3})*)/g);
    const prices = [];
    
    if (priceMatches) {
      priceMatches.forEach(match => {
        const price = parseInt(match.replace(/[$,\s]/g, ''));
        if (price >= 200 && price <= 10000) { // Reasonable flight prices
          prices.push(price);
        }
      });
    }
    
    console.log(`💰 Found ${prices.length} price candidates`);
    
    // Parse flights from page text manually
    const flights = [];
    const lines = pageText.split('\n');
    
    for (let i = 0; i < lines.length - 10; i++) {
      const line = lines[i].trim();
      
      // Look for departure time: "HH:MM AM/PM" on this line
      const deptMatch = line.match(/^(\d{1,2}:\d{2}\s*(?:AM|PM)?)$/);
      
      if (deptMatch) {
        // Next line should be " – "
        const separator = lines[i + 1]?.trim();
        if (separator !== '–' && separator !== '-') continue;
        
        // Next line should be arrival time
        const arrivalLine = lines[i + 2]?.trim() || '';
        const arrivalMatch = arrivalLine.match(/^(\d{1,2}:\d{2}\s*(?:AM|PM)?\+?\d*)$/);
        if (!arrivalMatch) continue;
        
        const departure = deptMatch[1];
        const arrival = arrivalMatch[1];
        
        // Next line should be airline(s)
        const airline = (lines[i + 3] || '').trim().substring(0, 60);
        
        // Next line should be duration
        const duration = (lines[i + 4] || '').trim();
        
        // Skip route line and look for stops
        const stopsLine = (lines[i + 6] || '').trim();
        
        // Next line (i+7) should be layover info if it has stops
        const layoverInfo = (lines[i + 7] || '').trim();
        // Only treat as layover if it matches pattern like "X hr Y min AIRPORT"
        const isLayoverLine = /^\d+\s*hr|\d+\s*min/.test(layoverInfo);
        const layoverDetail = isLayoverLine ? layoverInfo : '';
        
        // Search for price in the next 12 lines
        let price = 0;
        for (let j = i + 5; j < Math.min(i + 15, lines.length); j++) {
          const priceMatch = lines[j].match(/\$\s*([\d,]+)/);
          if (priceMatch) {
            price = parseInt(priceMatch[1].replace(/,/g, '')) || 0;
            break;
          }
        }
        
        // Only add if we found a valid price and key fields
        if (price > 1000 && price < 10000 && airline && duration) {
          flights.push({
            departure: departure,
            arrival: arrival,
            airline: airline,
            duration: duration,
            stops: stopsLine,
            layover: layoverDetail,
            price: price
          });
          
          i += 10; // Skip to next potential flight
        }
      }
    }
    
    console.log(`📦 Found ${flights.length} structured flights`);
    
    return {
      prices,
      pageText: pageText,
      flights: flights
    };
    
  } finally {
    await browser.close();
    console.log('✅ Browser closed');
  }
}

async function saveResults(data) {
  const uniquePrices = [...new Set(data.prices)].sort((a, b) => a - b);
  
  // Convert structured flights to proper format
  const flights = (data.flights || []).map(f => ({
    airline: f.airline,
    departure: f.departure,
    arrival: f.arrival,
    duration: f.duration,
    stops: f.stops,
    layover: f.layover || '',
    price: parseInt(f.price) || 0,
    booking_url: "https://www.google.com/travel/flights?q=Flights%20from%20SAN%20to%20ATH%20on%202026-06-12%20returning%202026-06-22%20for%202%20adults"
  }));
  
  const results = {
    timestamp: new Date().toISOString(),
    route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
    dates: {
      depart: CONFIG.trip.departDate,
      return: CONFIG.trip.returnDate
    },
    passengers: CONFIG.trip.passengers,
    flights: flights.slice(0, 5), // Top 5 structured flights
    stats: uniquePrices.length > 0 ? {
      count: uniquePrices.length,
      min: uniquePrices[0],
      max: uniquePrices[uniquePrices.length - 1],
      avg: Math.round(uniquePrices.reduce((a, b) => a + b) / uniquePrices.length),
      median: uniquePrices[Math.floor(uniquePrices.length / 2)],
      q1: uniquePrices[Math.floor(uniquePrices.length * 0.25)],
      q3: uniquePrices[Math.floor(uniquePrices.length * 0.75)]
    } : null,
    prices: uniquePrices,
    raw: data
  };
  
  // Save
  const today = new Date().toISOString().split('T')[0];
  const dataFile = path.join(BASE_DIR, 'data', `${today}.json`);
  fs.writeFileSync(dataFile, JSON.stringify(results, null, 2));
  
  // Append to history
  const historyFile = path.join(BASE_DIR, 'data', 'history.jsonl');
  fs.appendFileSync(historyFile, JSON.stringify(results) + '\n');
  
  console.log('\n📊 Flight Price Summary:');
  if (results.stats) {
    console.log(`   Lowest:  $${results.stats.min}`);
    console.log(`   Average: $${results.stats.avg}`);
    console.log(`   Highest: $${results.stats.max}`);
    console.log(`   Median:  $${results.stats.median}`);
    console.log(`   Found:   ${results.stats.count} prices`);
  } else {
    console.log('   ⚠️  No valid prices found');
  }
  
  console.log(`\n💾 Saved to: ${dataFile}`);
  
  return results;
}

async function main() {
  console.log('🛫 Flight Tracker starting...\n');
  
  try {
    const data = await scrapeFlights();
    const results = await saveResults(data);
    
    console.log('\n✨ Done!');
    return results;
  } catch (err) {
    console.error('\n❌ Error:', err.message);
    console.error(err.stack);
    throw err;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { main };
