#!/usr/bin/env node
/**
 * Automated Flight Tracker
 * Runs scraper and analyzes results
 * Called by cron jobs
 */

const fs = require('fs');
const path = require('path');
const { main: runScraper } = require('./scraper-final.js');

const BASE_DIR = __dirname;

async function checkForPriceDrops(latestData) {
  const historyFile = path.join(BASE_DIR, 'data', 'history.jsonl');
  
  if (!fs.existsSync(historyFile)) {
    console.log('📝 First run - no history to compare');
    return null;
  }
  
  // Read last 2 entries
  const lines = fs.readFileSync(historyFile, 'utf8').trim().split('\n');
  if (lines.length < 2) {
    return null;
  }
  
  const previous = JSON.parse(lines[lines.length - 2]);
  const current = latestData;
  
  if (!previous.stats || !current.stats) {
    return null;
  }
  
  const priceDrop = previous.stats.min - current.stats.min;
  const percentDrop = (priceDrop / previous.stats.min) * 100;
  
  if (percentDrop > 5) { // 5% or more drop
    return {
      drop: priceDrop,
      percent: percentDrop,
      was: previous.stats.min,
      now: current.stats.min
    };
  }
  
  return null;
}

async function generateAlert(alert) {
  console.log('\n🚨 PRICE ALERT! 🚨');
  console.log(`   Price dropped by $${alert.drop} (${alert.percent.toFixed(1)}%)`);
  console.log(`   Was: $${alert.was}`);
  console.log(`   Now: $${alert.now}`);
  console.log('');
  
  // Log to alerts file
  const alertsFile = path.join(BASE_DIR, 'alerts', 'price-drops.log');
  fs.mkdirSync(path.dirname(alertsFile), { recursive: true });
  
  const logEntry = `${new Date().toISOString()} | DROP: -$${alert.drop} (-${alert.percent.toFixed(1)}%) | ${alert.was} → ${alert.now}\n`;
  fs.appendFileSync(alertsFile, logEntry);
  
  return `🚨 FLIGHT PRICE ALERT!\n\nThe best price for SAN → ATH (June 12-22) just dropped!\n\n💰 Was: $${alert.was} per person\n✨ Now: $${alert.now} per person\n📉 Saved: $${alert.drop} (${alert.percent.toFixed(1)}%)\n\nCheck the dashboard: http://localhost:3737`;
}

async function main() {
  console.log('🛫 Auto-Track running...\n');
  
  try {
    // Run scraper
    const results = await runScraper();
    
    // Check for price drops
    const alert = await checkForPriceDrops(results);
    
    if (alert) {
      const message = await generateAlert(alert);
      console.log(message);
      
      // Return message so it gets sent to Telegram
      return message;
    } else {
      console.log('✅ Prices checked - no significant drops');
      
      if (results.stats) {
        console.log(`   Current best: $${results.stats.min} per person`);
      }
    }
    
  } catch (err) {
    console.error('❌ Auto-track failed:', err.message);
    throw err;
  }
}

if (require.main === module) {
  main()
    .then(result => {
      if (result) {
        console.log('\n' + result);
      }
      process.exit(0);
    })
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}

module.exports = { main };
