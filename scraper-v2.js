#!/usr/bin/env node
/**
 * Google Flights Scraper v2
 * Improved parsing for flight data
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BASE_DIR = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));

function buildGoogleFlightsUrl(origin, dest, date, returnDate = null) {
  // Simpler Google Flights URL format
  const outbound = `${origin}.${dest}.${date}`;
  const inbound = returnDate ? `.${dest}.${origin}.${returnDate}` : '';
  return `https://www.google.com/travel/flights/search?tfs=CBwQAhokagcIARIDU0FOEgoyMDI2LTA2LTEycgcIARIDQVRIMgoIMhAAGAAiA1VTRAoIAhAAGAAiA1VTRAoBYxABGAA&curr=USD`;
}

async function fetchWithWebFetch() {
  const url = buildGoogleFlightsUrl(
    CONFIG.trip.origin,
    CONFIG.trip.destination,
    CONFIG.trip.departDate,
    CONFIG.trip.returnDate
  );
  
  console.log(`📡 Fetching Google Flights...`);
  
  try {
    // For now, use direct URL approach
    // TODO: Use OpenClaw's web_fetch once Brave API is configured
    const html = execSync(
      `curl -s -A "Mozilla/5.0" "${url}"`,
      { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 }
    );
    
    return html;
  } catch (err) {
    console.error('❌ Fetch failed:', err.message);
    return null;
  }
}

function parseFlightData(html) {
  const results = {
    timestamp: new Date().toISOString(),
    route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
    date: CONFIG.trip.departDate,
    flights: []
  };
  
  // Look for embedded JSON data (Google often embeds flight data)
  const jsonMatches = html.match(/AF_initDataCallback\({[^}]+data:(\[[^\]]+\])/g);
  
  if (jsonMatches && jsonMatches.length > 0) {
    console.log(`📦 Found ${jsonMatches.length} data blocks`);
  }
  
  // Better price regex - look for prices in proper format
  const pricePattern = /\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/g;
  const prices = [];
  let match;
  
  while ((match = pricePattern.exec(html)) !== null) {
    const price = parseInt(match[1].replace(/,/g, ''));
    if (price > 100 && price < 10000) { // Filter out nonsense prices
      prices.push(price);
    }
  }
  
  if (prices.length > 0) {
    const uniquePrices = [...new Set(prices)].sort((a, b) => a - b);
    console.log(`💰 Found ${uniquePrices.length} unique prices: ${uniquePrices.slice(0, 5).join(', ')}...`);
    
    results.minPrice = Math.min(...uniquePrices);
    results.maxPrice = Math.max(...uniquePrices);
    results.avgPrice = Math.round(uniquePrices.reduce((a, b) => a + b) / uniquePrices.length);
    results.priceRange = uniquePrices;
  }
  
  return results;
}

async function saveData(data) {
  const today = new Date().toISOString().split('T')[0];
  const dataFile = path.join(BASE_DIR, 'data', `${today}.json`);
  const historyFile = path.join(BASE_DIR, 'data', 'history.jsonl');
  
  // Save daily snapshot
  fs.writeFileSync(dataFile, JSON.stringify(data, null, 2));
  
  // Append to history
  fs.appendFileSync(historyFile, JSON.stringify(data) + '\n');
  
  console.log(`✅ Saved to ${dataFile}`);
  console.log(`📊 Min: $${data.minPrice} | Avg: $${data.avgPrice} | Max: $${data.maxPrice}`);
}

async function main() {
  console.log('🛫 Flight Tracker v2 running...\n');
  
  const html = await fetchWithWebFetch();
  if (!html) return;
  
  const data = parseFlightData(html);
  await saveData(data);
  
  console.log('\n✨ Done!');
}

main().catch(console.error);
