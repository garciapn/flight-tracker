#!/usr/bin/env node
/**
 * Amadeus API Integration - Real Flight Data
 * Uses Amadeus API for authentic flight information
 */

const https = require('https');
const querystring = require('querystring');
require('dotenv').config();

const AMADEUS_CLIENT_ID = process.env.AMADEUS_CLIENT_ID;
const AMADEUS_CLIENT_SECRET = process.env.AMADEUS_CLIENT_SECRET;

class AmadeusAPI {
  constructor() {
    this.accessToken = null;
    this.tokenExpiry = 0;
  }

  /**
   * HTTPS request helper
   */
  async httpsRequest(options, body = null) {
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (res.statusCode >= 400) {
              const errMsg = parsed.errors ? JSON.stringify(parsed.errors) : JSON.stringify(parsed);
              reject(new Error(`HTTP ${res.statusCode}: ${errMsg}`));
            } else {
              resolve(parsed);
            }
          } catch (err) {
            reject(new Error(`Parse error: ${err.message} - Raw: ${data.substring(0, 200)}`));
          }
        });
      });

      req.on('error', reject);
      if (body) req.write(body);
      req.end();
    });
  }

  /**
   * Get OAuth 2.0 token
   */
  async authenticate() {
    console.log('[Amadeus] Authenticating...');
    
    const postData = querystring.stringify({
      grant_type: 'client_credentials',
      client_id: AMADEUS_CLIENT_ID,
      client_secret: AMADEUS_CLIENT_SECRET
    });

    const options = {
      hostname: 'api.amadeus.com',
      port: 443,
      path: '/v1/security/oauth20/token',
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const response = await this.httpsRequest(options, postData);
    
    if (!response.access_token) {
      throw new Error('No access token in response');
    }

    this.accessToken = response.access_token;
    this.tokenExpiry = Date.now() + ((response.expires_in - 60) * 1000);
    console.log('[Amadeus] ✅ Token acquired');
    
    return this.accessToken;
  }

  /**
   * Search flight offers
   */
  async searchFlights(origin, destination, departDate, returnDate = null, adults = 1) {
    // Get fresh token
    await this.authenticate();

    const params = new URLSearchParams({
      originLocationCode: origin,
      destinationLocationCode: destination,
      departureDate: departDate,
      adults: adults,
      max: 50
    });

    if (returnDate) {
      params.append('returnDate', returnDate);
    }

    console.log(`[Amadeus] Searching ${origin}→${destination}`);

    const options = {
      hostname: 'api.amadeus.com',
      port: 443,
      path: `/v2/shopping/flight-offers?${params.toString()}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'User-Agent': 'FlightTracker/1.0'
      }
    };

    const response = await this.httpsRequest(options);
    return response;
  }

  /**
   * Format API response into readable flight data
   */
  formatFlights(response) {
    const flights = [];

    if (!response.data || !Array.isArray(response.data)) {
      console.log('[Amadeus] No data in response');
      return flights;
    }

    console.log(`[Amadeus] Processing ${response.data.length} offers...`);

    response.data.forEach((offer, idx) => {
      try {
        const itineraries = offer.itineraries;
        if (!itineraries || itineraries.length === 0) return;
        
        const outbound = itineraries[0];
        const inbound = itineraries[1] || null;
        
        if (!outbound.segments || outbound.segments.length === 0) return;

        const outboundFirst = outbound.segments[0];
        const inboundFirst = inbound?.segments[0] || null;

        const totalPrice = parseFloat(offer.price.total);
        const numTravelers = offer.travelerPricings?.length || 1;
        const pricePerPerson = totalPrice / numTravelers;

        flights.push({
          id: idx + 1,
          price: Math.round(totalPrice),
          pricePerPerson: Math.round(pricePerPerson * 100) / 100,
          currency: offer.price.currency || 'USD',
          airline: outboundFirst.operating?.carrierCode || outboundFirst.carrierCode || 'Unknown',
          departure: outboundFirst.departure?.at || 'N/A',
          arrival: outboundFirst.arrival?.at || 'N/A',
          duration: outbound.duration || 'N/A',
          stops: Math.max(0, outbound.segments.length - 1),
          source: 'amadeus',
          raw: offer
        });
      } catch (err) {
        console.warn(`[Amadeus] Parse error on offer ${idx}:`, err.message);
      }
    });

    return flights;
  }
}

module.exports = AmadeusAPI;
