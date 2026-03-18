#!/usr/bin/env node
/**
 * Google Flights Scraper
 * Uses Puppeteer to scrape REAL flight data from Google Flights
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class GoogleFlightsScraper {
  constructor() {
    this.browser = null;
    this.timeout = 30000;
  }

  async launch() {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
    }
    return this.browser;
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Build Google Flights URL
   */
  buildUrl(origin, destination, departDate, returnDate, passengers = 1) {
    // Google Flights URL format (simplified search)
    const baseUrl = 'https://www.google.com/travel/flights';
    
    // Format: f.0.t.SAN.ATH.2026-06-12.1.t.ATH.SAN.2026-06-22
    let tfs = `f.0.t.${origin}.${destination}.${departDate}`;
    if (returnDate) {
      tfs += `.1.t.${destination}.${origin}.${returnDate}`;
    }
    
    const params = new URLSearchParams({
      tfs: tfs,
      tg: 0
    });

    return `${baseUrl}?${params.toString()}`;
  }

  /**
   * Scrape flights from Google Flights
   */
  async scrapeFlights(origin, destination, departDate, returnDate = null, passengers = 1, maxWaitTime = 15000) {
    await this.launch();
    const page = await this.browser.newPage();
    
    // Set reasonable viewport
    await page.setViewport({ width: 1280, height: 800 });
    
    const url = this.buildUrl(origin, destination, departDate, returnDate, passengers);
    console.log(`🔍 Scraping: ${url}`);

    try {
      // Navigate and wait for content
      await page.goto(url, { waitUntil: 'networkidle0', timeout: this.timeout });

      // Wait for flight results to load
      const startTime = Date.now();
      while (Date.now() - startTime < maxWaitTime) {
        const flightCount = await page.evaluate(() => {
          const elements = document.querySelectorAll('[data-test-id="fare-card"]');
          return elements.length;
        });

        if (flightCount > 0) {
          console.log(`✅ Found ${flightCount} flight cards`);
          break;
        }

        await new Promise(r => setTimeout(r, 1000));
      }

      // Extract flight data
      const flights = await page.evaluate(() => {
        const results = [];
        const cards = document.querySelectorAll('[data-test-id="fare-card"]');

        cards.forEach((card, idx) => {
          try {
            // Price
            const priceEl = card.querySelector('[data-test-id="price"]');
            let price = null;
            if (priceEl) {
              const text = priceEl.textContent.replace(/[^\d]/g, '');
              price = parseInt(text);
            }

            // Airlines
            const airlineEls = card.querySelectorAll('[data-test-id="airline-logo"] span');
            const airlines = Array.from(airlineEls).map(el => el.textContent.trim()).join(', ') || 'Unknown';

            // Duration & stops
            const durationEl = card.querySelector('[data-test-id="flight-duration"]');
            const duration = durationEl ? durationEl.textContent.trim() : 'Unknown';

            const stopsEl = card.querySelector('[data-test-id="flight-stops"]');
            const stops = stopsEl ? stopsEl.textContent.trim() : '0 stops';

            // Departure/arrival times
            const timeEl = card.querySelector('[data-test-id="departure-time"]');
            const arrivalEl = card.querySelector('[data-test-id="arrival-time"]');
            const depTime = timeEl ? timeEl.textContent.trim() : '';
            const arrTime = arrivalEl ? arrivalEl.textContent.trim() : '';

            if (price && price > 0) {
              results.push({
                price,
                airlines,
                duration,
                stops,
                departure: depTime,
                arrival: arrTime,
                url: window.location.href
              });
            }
          } catch (e) {
            console.error('Parse error:', e.message);
          }
        });

        return results.slice(0, 50);  // Return top 50
      });

      await page.close();
      return flights;

    } catch (err) {
      console.error('❌ Scrape error:', err.message);
      await page.close();
      return [];
    }
  }
}

module.exports = GoogleFlightsScraper;
