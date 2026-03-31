# 🤖 Flight Tracker Automation Summary

## ✅ Active Automations

### 📅 Daily Price Checks (2x per day)

**Morning Check** - 8:00 AM PST
- Runs: Every day at 8am
- Action: Scrapes Google Flights for current prices
- Alert: Sends Telegram message if price drops >5%
- Next run: Check `/openclaw cron list`

**Evening Check** - 8:00 PM PST  
- Runs: Every day at 8pm
- Action: Scrapes Google Flights for current prices
- Alert: Sends Telegram message if price drops >5%
- Next run: Check `/openclaw cron list`

### 📊 Weekly Report - Sundays at 8:00 PM PST

**What It Does:**
- Analyzes all price data from the past 7 days
- Calculates trends (rising/falling/stable)
- Identifies lowest/highest prices of the week
- Generates actionable recommendations
- Sends full report to your Telegram

**Report Includes:**
- 💰 Best price this week
- 📊 Average & highest prices
- 📈 Price movement (% change)
- 🌊 Volatility analysis
- 💡 Smart recommendations
- 📅 Days until departure countdown
- 📊 Booking window advice

**Sample Report:**
```
📊 Weekly Flight Report
🛫 SAN → ATH (June 12-22, 2026)

This Week's Summary:
━━━━━━━━━━━━━━━━━━━
💰 Best Price: $2377 ($1189/person)
📊 Average: $3179 ($1590/person)
📈 Highest: $2377 ($1189/person)

Price Movement:
➡️ Stable
+$0 (+0.0%) vs. last week

Volatility: $0 spread
Checks: 2 this week

━━━━━━━━━━━━━━━━━━━
💡 Recommendations:

• 🟡 Prices are stable. Continue monitoring.
• ✅ Low volatility - prices are stable.

━━━━━━━━━━━━━━━━━━━
📱 Dashboard: http://localhost:3737
⏰ Next report: Same time next week
```

---

## 🗓️ Schedule Overview

| Time | Day | Action | Delivery |
|------|-----|--------|----------|
| 8:00 AM | Daily | Price Check | Telegram (if alert) |
| 8:00 PM | Daily | Price Check | Telegram (if alert) |
| 8:00 PM | Sundays | Weekly Report | Telegram (always) |

---

## 🚨 Alert Triggers

### Price Drop Alert (Daily)
**Condition:** Price drops >5% from previous check  
**Format:**
```
🚨 FLIGHT PRICE ALERT!

The best price for SAN → ATH (June 12-22) just dropped!

💰 Was: $2,403 per person
✨ Now: $2,299 per person
📉 Saved: $104 (4.3%)

Check the dashboard: http://localhost:3737
```

### Weekly Report (Sundays)
**Condition:** Always sent, regardless of price movement  
**Content:** Full week analysis + recommendations

---

## 📊 Data Storage

All automation runs are logged:

```
data/
├── YYYY-MM-DD.json       # Daily snapshots
├── history.jsonl         # Complete timeline
├── screenshots/          # Google Flights screenshots
└── page-text-latest.txt  # Raw scraped content

alerts/
└── price-drops.log       # Price drop event log

reports/
└── week-of-YYYY-MM-DD.md # Weekly reports archive
```

---

## 🛠️ Manual Triggers

You can run any automation manually:

```bash
cd /Users/gerald/.openclaw/workspace/flight-tracker

# Daily check
npm run track

# Weekly report
npm run report

# Price scrape only (no alerts)
npm run scrape
```

---

## 📲 Telegram Message Examples

### Daily Alert (Price Drop)
Sent only when price drops >5%

### Weekly Report
Sent every Sunday at 8pm, regardless of price movement

---

## ⚙️ Customization

### Change Alert Threshold
Edit `auto-track.js`:
```javascript
if (percentDrop > 5) { // Change to 3, 10, etc.
```

### Change Weekly Report Day/Time
```bash
openclaw cron list
# Find "Flight Tracker - Weekly Report" job ID
openclaw cron update <job-id> --schedule "0 20 * * 6"  # Saturday 8pm
```

### Modify Report Content
Edit `weekly-report.js` - customize recommendations, formatting, etc.

---

## 🔍 Monitoring

### Check Automation Status
```bash
# List all cron jobs
openclaw cron list

# View recent runs
openclaw cron runs <job-id>
```

### View Logs
```bash
# Price check history
cat data/history.jsonl | tail -10

# Alert history
cat alerts/price-drops.log

# Recent reports
ls -lh reports/
```

---

## 🎯 Next Enhancements (Optional)

### Potential Additions:
- [ ] Mid-week mini-report (Wednesday check-in)
- [ ] Month-end summary with best booking window
- [ ] Points calculator integration
- [ ] Multi-route tracking (add Santorini, Mykonos)
- [ ] Email delivery option
- [ ] SMS alerts for critical drops (>10%)

---

## 🚀 Status

**All Systems Operational** 🟢

- ✅ Daily tracking: Active
- ✅ Weekly reports: Scheduled
- ✅ Telegram delivery: Configured
- ✅ Dashboard: Running on :3737
- ✅ Data logging: Active

**Next Events:**
- Daily check: Tomorrow 8:00 AM
- Weekly report: Sunday 8:00 PM

---

Built by Gerald ⚡ for User's Greece adventure 🇬🇷
