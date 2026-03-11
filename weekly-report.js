#!/usr/bin/env node
/**
 * Weekly Flight Tracker Report Generator
 * Analyzes the week's data and creates a summary
 */

const fs = require('fs');
const path = require('path');

const BASE_DIR = __dirname;

function readHistory() {
  const historyFile = path.join(BASE_DIR, 'data', 'history.jsonl');
  
  if (!fs.existsSync(historyFile)) {
    return [];
  }
  
  const lines = fs.readFileSync(historyFile, 'utf8').trim().split('\n');
  return lines.map(line => {
    try {
      return JSON.parse(line);
    } catch {
      return null;
    }
  }).filter(Boolean);
}

function getLastWeekData(history) {
  const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
  return history.filter(entry => {
    const entryTime = new Date(entry.timestamp).getTime();
    return entryTime >= weekAgo;
  });
}

function analyzeTrends(weekData) {
  if (weekData.length === 0) {
    return null;
  }
  
  const prices = weekData
    .filter(d => d.stats && d.stats.min)
    .map(d => ({
      date: new Date(d.timestamp).toLocaleDateString(),
      min: d.stats.min,
      avg: d.stats.avg,
      max: d.stats.max
    }));
  
  if (prices.length === 0) {
    return null;
  }
  
  // Calculate trends
  const allMinPrices = prices.map(p => p.min);
  const allAvgPrices = prices.map(p => p.avg);
  
  const weekLow = Math.min(...allMinPrices);
  const weekHigh = Math.max(...allMinPrices);
  const weekAvg = Math.round(allAvgPrices.reduce((a, b) => a + b) / allAvgPrices.length);
  
  // Price direction
  const firstPrice = allMinPrices[0];
  const lastPrice = allMinPrices[allMinPrices.length - 1];
  const weekChange = lastPrice - firstPrice;
  const weekChangePercent = ((weekChange / firstPrice) * 100).toFixed(1);
  
  // Volatility
  const volatility = weekHigh - weekLow;
  
  return {
    weekLow,
    weekHigh,
    weekAvg,
    weekChange,
    weekChangePercent,
    volatility,
    checksThisWeek: weekData.length,
    priceHistory: prices,
    trend: weekChange > 0 ? '📈 Rising' : weekChange < 0 ? '📉 Falling' : '➡️ Stable'
  };
}

function generateRecommendations(trends) {
  const recommendations = [];
  
  if (!trends) {
    return ['Not enough data yet - check back next week!'];
  }
  
  // Price movement recommendations
  if (parseFloat(trends.weekChangePercent) < -3) {
    recommendations.push('🟢 Prices are falling! Good time to keep watching closely.');
  } else if (parseFloat(trends.weekChangePercent) > 3) {
    recommendations.push('🔴 Prices are rising! Consider booking if you see a good deal.');
  } else {
    recommendations.push('🟡 Prices are stable. Continue monitoring for sudden drops.');
  }
  
  // Volatility recommendations
  if (trends.volatility > 500) {
    recommendations.push('⚠️ High price volatility this week - check multiple times daily.');
  } else if (trends.volatility < 100) {
    recommendations.push('✅ Low volatility - prices are stable.');
  }
  
  // Best price recommendation
  if (trends.weekLow < 2200) {
    recommendations.push('🎯 Excellent prices seen this week! Under $1,100/person is a great deal.');
  } else if (trends.weekLow > 2800) {
    recommendations.push('💰 Prices are high right now. Wait for a drop before booking.');
  }
  
  // Days until departure recommendation (if we have config)
  try {
    const config = JSON.parse(fs.readFileSync(path.join(BASE_DIR, 'config.json'), 'utf8'));
    const departDate = new Date(config.trip.departDate);
    const daysUntil = Math.floor((departDate - Date.now()) / (24 * 60 * 60 * 1000));
    
    if (daysUntil > 120) {
      recommendations.push('⏰ Still early - prices may drop further. No rush to book.');
    } else if (daysUntil < 60) {
      recommendations.push('⚡ Less than 60 days out - book soon if you see a good price!');
    }
  } catch (err) {
    // Config read failed, skip this recommendation
  }
  
  return recommendations;
}

function formatTelegramReport(trends, recommendations) {
  if (!trends) {
    return `📊 **Weekly Flight Report**
    
🛫 SAN → ATH (June 12-22)

Not enough data collected yet. Check back next week!

Dashboard: http://localhost:3737`;
  }
  
  const report = `📊 **Weekly Flight Report**
🛫 SAN → ATH (June 12-22, 2026)

**This Week's Summary:**
━━━━━━━━━━━━━━━━━━━
💰 **Best Price**: $${trends.weekLow} ($${Math.round(trends.weekLow/2)}/person)
📊 **Average**: $${trends.weekAvg} ($${Math.round(trends.weekAvg/2)}/person)
📈 **Highest**: $${trends.weekHigh} ($${Math.round(trends.weekHigh/2)}/person)

**Price Movement:**
${trends.trend}
${trends.weekChange >= 0 ? '+' : ''}$${Math.abs(trends.weekChange)} (${trends.weekChangePercent >= 0 ? '+' : ''}${trends.weekChangePercent}%) vs. last week

**Volatility**: $${trends.volatility} spread
**Checks**: ${trends.checksThisWeek} this week

━━━━━━━━━━━━━━━━━━━
**💡 Recommendations:**

${recommendations.map(r => `• ${r}`).join('\n')}

━━━━━━━━━━━━━━━━━━━
📱 Dashboard: http://localhost:3737
⏰ Next report: Same time next week

Tracking by Gerald ⚡`;

  return report;
}

function saveReport(report, trends) {
  const reportsDir = path.join(BASE_DIR, 'reports');
  fs.mkdirSync(reportsDir, { recursive: true });
  
  const weekOf = new Date().toISOString().split('T')[0];
  const filename = `week-of-${weekOf}.md`;
  
  const markdown = `# Weekly Flight Report - ${weekOf}

${report}

## Detailed Data

${trends ? `
### Price History This Week
${trends.priceHistory.map(p => `- ${p.date}: $${p.min} (avg: $${p.avg})`).join('\n')}

### Statistics
- Lowest: $${trends.weekLow}
- Highest: $${trends.weekHigh}
- Average: $${trends.weekAvg}
- Volatility: $${trends.volatility}
- Trend: ${trends.trend}
- Change: ${trends.weekChangePercent}%
` : 'Insufficient data'}

---
*Generated on ${new Date().toLocaleString()}*
`;
  
  fs.writeFileSync(path.join(reportsDir, filename), markdown);
  console.log(`✅ Report saved: ${filename}`);
}

async function main() {
  console.log('📊 Generating weekly flight report...\n');
  
  try {
    const history = readHistory();
    console.log(`📚 Loaded ${history.length} historical entries`);
    
    const weekData = getLastWeekData(history);
    console.log(`📅 Analyzing last ${weekData.length} entries from this week\n`);
    
    const trends = analyzeTrends(weekData);
    const recommendations = generateRecommendations(trends);
    
    const report = formatTelegramReport(trends, recommendations);
    
    // Save report
    saveReport(report, trends);
    
    // Print report (this will be sent via Telegram by the cron job)
    console.log(report);
    
    // Return for Telegram delivery
    return report;
    
  } catch (err) {
    console.error('❌ Report generation failed:', err.message);
    throw err;
  }
}

if (require.main === module) {
  main()
    .then(report => {
      process.exit(0);
    })
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}

module.exports = { main };
