#!/usr/bin/env node
/**
 * Flight Tracker for SAN → ATH
 * Checks flight prices, logs data, sends alerts
 */

const fs = require('fs');
const path = require('path');

const BASE_DIR = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));

// Placeholder for flight data fetching
async function fetchFlights() {
  // TODO: Integrate with Kiwi.com or Amadeus API
  // For now, return mock data structure
  return {
    timestamp: new Date().toISOString(),
    route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
    date: CONFIG.trip.departDate,
    flights: [
      {
        price: 850,
        currency: 'USD',
        airline: 'Delta',
        stops: 1,
        duration: '16h 30m',
        layover: 'JFK',
        layoverDuration: '2h 15m',
        departure: '2026-06-12T10:00:00',
        arrival: '2026-06-13T08:30:00+03:00'
      }
    ]
  };
}

async function analyzeAndAlert(data) {
  const dataDir = path.join(BASE_DIR, 'data');
  const historyFile = path.join(dataDir, 'history.jsonl');
  
  // Log to history
  fs.appendFileSync(historyFile, JSON.stringify(data) + '\n');
  
  // Save daily snapshot
  const today = new Date().toISOString().split('T')[0];
  fs.writeFileSync(
    path.join(dataDir, `${today}.json`),
    JSON.stringify(data, null, 2)
  );
  
  console.log(`✅ Tracked ${data.flights.length} flights at ${data.timestamp}`);
  
  // TODO: Compare with previous prices, send alerts
}

async function main() {
  console.log('🛫 Flight Tracker running...');
  const data = await fetchFlights();
  await analyzeAndAlert(data);
  console.log('✅ Done!');
}

main().catch(console.error);
