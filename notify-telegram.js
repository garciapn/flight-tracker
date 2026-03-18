#!/usr/bin/env node
/**
 * Telegram Notification
 * Sends flight results to Paolo via OpenClaw message tool
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config();

/**
 * Format flight results for Telegram
 */
function formatFlightResults(results) {
  const { topFlights, summary, route, departure, return: returnDate, passengers } = results;

  let message = `🛫 *Flight Search Results*\n\n`;
  message += `*Route:* ${route}\n`;
  message += `*Dates:* ${departure} to ${returnDate}\n`;
  message += `*Passengers:* ${passengers}\n\n`;

  message += `📊 *Summary*\n`;
  message += `Total found: ${summary.totalFound}\n`;
  message += `Price range: $${summary.priceRange.min} - $${summary.priceRange.max}\n`;
  message += `Average: $${summary.priceRange.avg}\n\n`;

  message += `✈️ *Top 15 Options*\n`;
  message += `━━━━━━━━━━━━━━━━━━━━\n\n`;

  topFlights.forEach((flight, idx) => {
    message += `*${idx + 1}. $${flight.price}* (${flight.currency})\n`;
    message += `   💵 Per person: $${flight.pricePerPerson}\n`;
    message += `   ✈️ ${flight.airline || 'Mixed'}\n`;
    
    if (flight.duration) {
      message += `   ⏱️ Duration: ${flight.duration}\n`;
    }
    if (flight.stops) {
      message += `   🛑 ${flight.stops}\n`;
    }
    if (flight.departure) {
      message += `   🕐 Depart: ${flight.departure}\n`;
    }
    
    message += `\n`;
  });

  message += `━━━━━━━━━━━━━━━━━━━━\n`;
  message += `💡 *Recommendation:* Book at ~$${summary.recommendedBudget} for good value\n`;
  message += `⏰ *Found:* ${new Date().toLocaleString()}\n`;

  return message;
}

/**
 * Send message via OpenClaw message tool
 * This leverages the main agent's message tool
 */
async function sendViaTelegram(message, telegramId = '5851420265') {
  console.log('📤 Sending to Telegram...');
  
  // In production, this would be called via the message tool
  // For this subagent context, we return the message for the parent to send
  console.log('Message ready for Telegram:');
  console.log(message);
  
  return message;
}

async function main() {
  // Read the latest flight results
  const dataDir = path.join(__dirname, 'data');
  const files = fs.readdirSync(dataDir)
    .filter(f => f.startsWith('flights-') && f.endsWith('.json'))
    .sort()
    .reverse();

  if (files.length === 0) {
    console.error('❌ No flight data found. Run search-flights.js first.');
    process.exit(1);
  }

  const latestFile = path.join(dataDir, files[0]);
  const results = JSON.parse(fs.readFileSync(latestFile, 'utf8'));

  const message = formatFlightResults(results);
  await sendViaTelegram(message);

  // Save formatted message
  const messageFile = path.join(dataDir, 'latest-message.txt');
  fs.writeFileSync(messageFile, message);
  console.log(`\n✅ Message saved to ${messageFile}`);
}

module.exports = { formatFlightResults, sendViaTelegram };

if (require.main === module) {
  main().catch(console.error);
}
