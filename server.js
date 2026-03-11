#!/usr/bin/env node
/**
 * Flight Tracker Dashboard Server
 * Serves the web dashboard and provides API endpoints
 */

const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3737;
const BASE_DIR = __dirname;

// Serve static files from dashboard directory
app.use(express.static(path.join(BASE_DIR, 'dashboard')));

// API endpoint for flight data
app.get('/api/data', (req, res) => {
  try {
    // Read latest data
    const dataDir = path.join(BASE_DIR, 'data');
    const files = fs.readdirSync(dataDir)
      .filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.json$/))
      .sort()
      .reverse();
    
    if (files.length === 0) {
      return res.json({
        latest: null,
        history: [],
        flights: []
      });
    }
    
    // Get latest
    const latestFile = path.join(dataDir, files[0]);
    const latest = JSON.parse(fs.readFileSync(latestFile, 'utf8'));
    
    // Get history (last 30 days)
    const history = files.slice(0, 30).map(file => {
      try {
        return JSON.parse(fs.readFileSync(path.join(dataDir, file), 'utf8'));
      } catch (err) {
        return null;
      }
    }).filter(Boolean);
    
    // Use structured flights if available, otherwise parse from page text
    const flights = (latest.flights && latest.flights.length > 0) 
      ? latest.flights 
      : parseFlightsFromText(latest.raw?.pageText || '');
    
    res.json({
      latest,
      history,
      flights
    });
    
  } catch (err) {
    console.error('API error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Helper to parse flights from scraped text
function parseFlightsFromText(text) {
  const flights = [];
  
  // Extract flight patterns from the text
  const flightPattern = /(\d{1,2}:\d{2} [AP]M)\s*–\s*(\d{1,2}:\d{2} [AP]M\+?\d?)[^$]*?\$(\d{1,3}(?:,\d{3})*)/g;
  const matches = [...text.matchAll(flightPattern)];
  
  matches.forEach((match, idx) => {
    const [_, departure, arrival, price] = match;
    
    // Try to extract airline
    const before = text.substring(Math.max(0, match.index - 200), match.index);
    const airlineMatch = before.match(/(Air Canada|United|Lufthansa|Alaska|American|British Airways|Delta|Finnair|Iberia|Aegean)/);
    
    // Extract duration
    const durationMatch = text.substring(match.index, match.index + 300).match(/(\d{1,2} hr(?: \d{1,2} min)?)/);
    
    // Extract stops
    const stopsMatch = text.substring(match.index, match.index + 200).match(/(\d+) stop/);
    
    // Extract layover
    const layoverMatch = text.substring(match.index, match.index + 300).match(/(\d+ hr(?: \d+ min)?) ([A-Z]{3})/);
    
    if (flights.length < 8) { // Only top 8 flights
      flights.push({
        departure: departure,
        arrival: arrival,
        price: parseInt(price.replace(/,/g, '')),
        airline: airlineMatch ? airlineMatch[1] : 'Unknown',
        duration: durationMatch ? durationMatch[1] : 'N/A',
        stops: stopsMatch ? `${stopsMatch[1]} stop` : '1 stop',
        layover: layoverMatch ? `${layoverMatch[1]} ${layoverMatch[2]}` : 'Unknown'
      });
    }
  });
  
  // Sort by price
  return flights.sort((a, b) => a.price - b.price);
}

// Search endpoint - redirects to Google Flights
app.get('/search', (req, res) => {
  // Build Google Flights search URL
  const origin = 'SAN';
  const destination = 'ATH';
  const departDate = '2026-06-12';
  const returnDate = '2026-06-22';
  const passengers = '2';
  
  const googleFlightsUrl = `https://www.google.com/travel/flights?q=Flights from ${origin} to ${destination} on ${departDate} returning ${returnDate} for ${passengers} adults`;
  
  res.redirect(googleFlightsUrl);
});

// API endpoint to get Google Flights URL for a specific flight
app.get('/api/google-flights-url', (req, res) => {
  const origin = req.query.origin || 'SAN';
  const destination = req.query.destination || 'ATH';
  const departDate = req.query.depart || '2026-06-12';
  const returnDate = req.query.return || '2026-06-22';
  const passengers = req.query.passengers || '2';
  
  const googleFlightsUrl = `https://www.google.com/travel/flights?q=Flights from ${origin} to ${destination} on ${departDate} returning ${returnDate} for ${passengers} adults`;
  
  res.json({ url: googleFlightsUrl });
});

// API endpoint to fetch real Google Flights prices
app.get('/api/google-flights-prices', async (req, res) => {
  try {
    const { spawn } = require('child_process');
    
    const process = spawn('node', [path.join(BASE_DIR, 'fetch-google-flights-simple.js')], {
      timeout: 35000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let stdout = '';
    let stderr = '';
    
    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    process.on('close', (code) => {
      try {
        if (code === 0 && stdout.trim()) {
          const jsonMatch = stdout.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const data = JSON.parse(jsonMatch[0]);
            res.json(data);
          } else {
            res.status(500).json({ error: 'Failed to parse Google Flights data' });
          }
        } else {
          res.status(500).json({ error: 'Google Flights scraper failed', stderr: stderr.substring(0, 200) });
        }
      } catch (e) {
        res.status(500).json({ error: 'Error processing Google Flights data: ' + e.message });
      }
    });
    
    // Timeout after 40 seconds
    setTimeout(() => {
      if (process.exitCode === null) {
        process.kill();
        res.status(408).json({ error: 'Google Flights fetch timeout' });
      }
    }, 40000);
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`\n✨ Flight Tracker Dashboard`);
  console.log(`   🌐 http://localhost:${PORT}`);
  console.log(`   📊 API: http://localhost:${PORT}/api/data`);
  console.log(`\n   Press Ctrl+C to stop\n`);
});
