#!/usr/bin/env node
/**
 * Telegram Notifier
 * Sends flight results to Paolo via OpenClaw message integration
 */

const fs = require('fs');
const path = require('path');

/**
 * Format results for Telegram
 */
function formatForTelegram(results) {
  const { trip, summary, flights } = results;
  
  let msg = `🛫 *FLIGHT SEARCH COMPLETE*\n\n`;
  msg += `*Route:* ${trip.origin} → ${trip.destination}\n`;
  msg += `*Dates:* ${trip.departure} to ${trip.return}\n`;
  msg += `*Passengers:* ${trip.passengers}\n\n`;

  msg += `📊 *PRICE SUMMARY*\n`;
  msg += `Min: $${summary.minPrice} | Max: $${summary.maxPrice}\n`;
  msg += `Avg: $${summary.avgPrice} | Median: $${summary.medianPrice}\n`;
  msg += `Recommended Budget: $${summary.recommendedBudget}\n\n`;

  msg += `🏆 *TOP 15 FLIGHTS*\n`;
  msg += `━━━━━━━━━━━━━━━━━━━━\n\n`;

  flights.forEach(f => {
    msg += `*#${f.rank}* - *$${f.price}* (${f.currency})\n`;
    msg += `💵 Per person: $${f.pricePerPerson}\n`;
    msg += `✈️ ${f.airline}\n`;
    msg += `⏱️ ${f.duration} | ${f.stops}\n`;
    msg += `🕐 ${f.departure} → ${f.arrival}\n`;
    msg += `\n`;
  });

  msg += `━━━━━━━━━━━━━━━━━━━━\n`;
  msg += `_Last updated: ${new Date().toLocaleString()}_\n`;

  return msg;
}

/**
 * Send notification
 * For subagent context, this returns formatted message
 */
async function sendNotification(results, targetUser = 'Paolo') {
  const message = formatForTelegram(results);
  
  console.log('\n📤 TELEGRAM MESSAGE READY:\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(message);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Save to file for reference
  const dataDir = path.join(__dirname, 'data');
  const msgFile = path.join(dataDir, 'latest-telegram-message.txt');
  fs.writeFileSync(msgFile, message);

  return message;
}

/**
 * Main
 */
async function main() {
  const dataDir = path.join(__dirname, 'data');
  
  // Find latest results
  const files = fs.readdirSync(dataDir)
    .filter(f => f.startsWith('flights-') && f.endsWith('.json'))
    .sort()
    .reverse();

  if (files.length === 0) {
    console.error('❌ No flight data found. Run search-flights-final.js first.');
    process.exit(1);
  }

  const latestFile = path.join(dataDir, files[0]);
  console.log(`📖 Loading: ${files[0]}`);
  
  const results = JSON.parse(fs.readFileSync(latestFile, 'utf8'));
  await sendNotification(results);

  console.log(`✅ Message ready to send to Paolo (5851420265)`);
}

module.exports = { formatForTelegram, sendNotification };

if (require.main === module) {
  main().catch(console.error);
}
