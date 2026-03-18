#!/usr/bin/env node
/**
 * Flight Search Script
 * Integrates Amadeus API + Google Flights scraper
 * Returns top 15 real flights with verified prices
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config();

const AmadeusAPI = require('./amadeus-api');
const GoogleFlightsScraper = require('./google-flights-scraper');

const CONFIG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));

class FlightSearchEngine {
  constructor() {
    this.amadeus = new AmadeusAPI();
    this.googleScraper = new GoogleFlightsScraper();
    this.allFlights = [];
  }

  /**
   * Search via Amadeus API (primary source - most reliable)
   */
  async searchAmadeus() {
    console.log('🔍 Searching Amadeus API...');
    try {
      const response = await this.amadeus.searchFlights(
        CONFIG.trip.origin,
        CONFIG.trip.destination,
        CONFIG.trip.departDate,
        CONFIG.trip.returnDate,
        CONFIG.trip.passengers
      );

      const flights = this.amadeus.formatFlights(response);
      console.log(`✅ Amadeus: Found ${flights.length} flights`);
      return flights;
    } catch (err) {
      console.error('❌ Amadeus search failed:', err.message);
      return [];
    }
  }

  /**
   * Search via Google Flights scraper (fallback/verification)
   */
  async searchGoogleFlights() {
    console.log('🔍 Scraping Google Flights...');
    try {
      const flights = await this.googleScraper.scrapeFlights(
        CONFIG.trip.origin,
        CONFIG.trip.destination,
        CONFIG.trip.departDate,
        CONFIG.trip.returnDate,
        CONFIG.trip.passengers
      );

      const formatted = flights.map((f, idx) => ({
        id: `gf-${idx + 1}`,
        price: f.price,
        pricePerPerson: Math.round(f.price / CONFIG.trip.passengers),
        currency: 'USD',
        airline: f.airlines,
        departure: f.departure,
        arrival: f.arrival,
        duration: f.duration,
        stops: f.stops,
        source: 'google_flights'
      }));

      console.log(`✅ Google Flights: Found ${formatted.length} flights`);
      return formatted;
    } catch (err) {
      console.error('❌ Google Flights scrape failed:', err.message);
      return [];
    }
  }

  /**
   * Deduplicate and rank flights by price
   */
  deduplicateAndRank(flights) {
    const seen = new Set();
    const deduped = [];

    // Sort by price ascending
    const sorted = flights.sort((a, b) => a.price - b.price);

    sorted.forEach(flight => {
      // Create signature: price ± 10 + airline + rough time
      const sig = `${Math.floor(flight.price / 10)}|${flight.airline}`;
      
      if (!seen.has(sig)) {
        seen.add(sig);
        deduped.push(flight);
      }
    });

    return deduped.slice(0, 15);  // Top 15
  }

  /**
   * Run full search
   */
  async search() {
    console.log(`\n🛫 Flight Search: ${CONFIG.trip.origin} → ${CONFIG.trip.destination}`);
    console.log(`📅 ${CONFIG.trip.departDate} to ${CONFIG.trip.returnDate}`);
    console.log(`👥 ${CONFIG.trip.passengers} passenger(s)\n`);

    const results = {
      timestamp: new Date().toISOString(),
      route: `${CONFIG.trip.origin} → ${CONFIG.trip.destination}`,
      departure: CONFIG.trip.departDate,
      return: CONFIG.trip.returnDate,
      passengers: CONFIG.trip.passengers,
      sources: {
        amadeus: [],
        googleFlights: []
      },
      topFlights: [],
      summary: {}
    };

    try {
      // Search Amadeus (primary)
      const amadeusFlights = await this.searchAmadeus();
      results.sources.amadeus = amadeusFlights;

      // Search Google Flights (verification/fallback)
      const googleFlights = await this.searchGoogleFlights();
      results.sources.googleFlights = googleFlights;

    } catch (err) {
      console.error('❌ Search error:', err.message);
    }

    // Combine and deduplicate
    const allFlights = [
      ...results.sources.amadeus,
      ...results.sources.googleFlights
    ];

    if (allFlights.length === 0) {
      console.error('❌ No flights found. Check API credentials and route.');
      return results;
    }

    const topFlights = this.deduplicateAndRank(allFlights);
    results.topFlights = topFlights;

    // Calculate summary
    const prices = topFlights.map(f => f.price);
    results.summary = {
      totalFound: allFlights.length,
      topOptions: topFlights.length,
      priceRange: {
        min: Math.min(...prices),
        max: Math.max(...prices),
        avg: Math.round(prices.reduce((a, b) => a + b, 0) / prices.length)
      },
      cheapestPerPerson: Math.round(topFlights[0]?.pricePerPerson || 0),
      recommendedBudget: Math.round(topFlights[Math.floor(topFlights.length / 2)]?.price || 0)
    };

    return results;
  }
}

// Main execution
async function main() {
  const engine = new FlightSearchEngine();
  const results = await engine.search();

  // Save results to file
  const dataDir = path.join(__dirname, 'data');
  if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

  const timestamp = new Date().toISOString().split('T')[0];
  const outputFile = path.join(dataDir, `flights-${timestamp}.json`);
  fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));

  console.log('\n📊 Results Summary:');
  console.log(`   Total flights found: ${results.summary.totalFound}`);
  console.log(`   Top options: ${results.summary.topOptions}`);
  console.log(`   Price range: $${results.summary.priceRange.min} - $${results.summary.priceRange.max}`);
  console.log(`   Cheapest per person: $${results.summary.cheapestPerPerson}`);
  console.log(`   Saved to: ${outputFile}\n`);

  // Also output JSON for easy parsing
  console.log('=== JSON OUTPUT ===');
  console.log(JSON.stringify(results, null, 2));

  // Clean up
  await engine.googleScraper.close();
}

main().catch(console.error);
