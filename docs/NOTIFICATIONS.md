# Notifications & Alerts Guide

Flight Tracker supports **5 notification channels**:
1. ✉️ Email
2. 📱 SMS (Twilio)
3. 💬 Slack
4. 🎮 Discord
5. 🔮 Price Predictions

---

## Email Alerts

### Setup

1. **Gmail (Recommended)**
   - Enable 2-factor authentication: https://myaccount.google.com/security
   - Create app password: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

2. **Configure**
   ```env
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx
   ```

3. **Test**
   ```bash
   python3 email_alerts.py
   # Edit the script to add your email
   ```

### Other Providers

| Provider | SMTP Server | Port | Notes |
|----------|------------|------|-------|
| Gmail | smtp.gmail.com | 587 | Use app password |
| Outlook | smtp.outlook.com | 587 | Use your password |
| Yahoo | smtp.mail.yahoo.com | 587 | Generate app password |
| SendGrid | smtp.sendgrid.net | 587 | Use `apikey` as username |

---

## SMS Alerts (Twilio)

### Setup

1. **Create Twilio Account**
   - Go to https://www.twilio.com
   - Sign up (free trial with $15 credit)
   - Create a new project

2. **Get Credentials**
   - Account SID: Starts with `AC...`
   - Auth Token: Your API key
   - Phone Number: Twilio number assigned to you

3. **Configure**
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+12025551234
   ```

4. **Install Twilio**
   ```bash
   pip install twilio
   ```

5. **Test**
   ```bash
   python3 sms_alerts.py
   # Edit script to add your phone number in E.164 format: +1234567890
   ```

### Pricing

- Outbound SMS: $0.0075 per message (varies by country)
- Free trial: $15 credit (~2,000 SMS)
- Perfect for: Daily alerts on 1-2 flights

### Format

Messages are optimized for SMS (160 characters):

```
✈️ FLIGHT DEAL! United, Air Canada: $1120/person (below $1200)! Save $80. Departs 06:30 AM. Check it out now!
```

---

## Slack Alerts

### Setup

1. **Create Webhook**
   - Go to your Slack workspace
   - Create app: https://api.slack.com/apps
   - Click "Incoming Webhooks"
   - Enable and "Add New Webhook to Workspace"
   - Select channel and authorize

2. **Get Webhook URL**
   - Copy the long URL: `https://hooks.slack.com/services/...`

3. **Configure**
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

4. **Test**
   ```bash
   python3 webhooks.py
   ```

### Message Format

Rich messages with:
- Airline
- Price & threshold
- Savings amount
- Flight details (departure, arrival, duration, layover)
- One-click booking link

### Advanced Setup

**Per-channel webhooks:**

```python
slack_alerts = {
    'budget': 'https://hooks.slack.com/services/.../budget_channel',
    'vip': 'https://hooks.slack.com/services/.../vip_channel'
}
```

---

## Discord Alerts

### Setup

1. **Create Webhook**
   - Open your Discord server
   - Right-click channel → Edit Channel
   - Go to Integrations → Webhooks
   - Click "New Webhook"
   - Copy the URL

2. **Get Webhook URL**
   - Format: `https://discordapp.com/api/webhooks/YOUR/WEBHOOK/URL`

3. **Configure**
   ```env
   DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR/WEBHOOK/URL
   ```

4. **Test**
   ```bash
   python3 webhooks.py
   ```

### Message Format

Beautiful embeds with:
- Purple gradient header
- Organized fields
- Price highlighted
- Savings calculated
- Flight details
- Timestamp

### Advanced

Multiple channels:

```python
discord_webhooks = {
    'general': 'https://discordapp.com/api/webhooks/...',
    'deals': 'https://discordapp.com/api/webhooks/...'
}
```

---

## Price Predictions

### How It Works

Uses historical price data to predict future trends:

1. **Collect** — Track prices daily
2. **Analyze** — Linear regression on 30+ days of data
3. **Predict** — Forecast prices 7 days ahead
4. **Recommend** — "Book now" vs "Wait" vs "Watch"

### Setup

No configuration needed! Just use it:

```bash
python3 price_predictor.py
```

### API Usage

```python
from price_predictor import PricePredictor

predictor = PricePredictor()

# Predict next 7 days
prediction = predictor.predict('United, Air Canada', days_ahead=7)

print(f"Current: ${prediction['current_price']}")
print(f"Predicted: ${prediction['prediction']}")
print(f"Trend: {prediction['trend']}")  # 'dropping', 'rising', 'stable'
print(f"Confidence: {prediction['confidence']}%")
```

### Booking Recommendation

```python
# Should I book now?
recommendation = predictor.get_best_booking_date('United, Air Canada')

print(recommendation['recommendation'])  # 'book_now', 'wait', 'book_soon'
print(recommendation['reason'])
```

### Prediction Confidence

- **< 30%**: Insufficient data, book when convenient
- **30-70%**: Moderate confidence, consider the trend
- **> 70%**: High confidence, follow recommendation

---

## Combining Notifications

Send to multiple channels simultaneously:

```python
from email_alerts import EmailAlerter
from sms_alerts import SMSAlerter
from webhooks import SlackWebhook, DiscordWebhook

alert_data = {
    'airline': 'United, Air Canada',
    'price': 1120,
    'threshold': 1200,
    'flight_details': {...}
}

# Send everywhere
EmailAlerter().send_alert(...)
SMSAlerter().send_alert('+15551234567', ...)
SlackWebhook().send_alert(...)
DiscordWebhook().send_alert(...)
```

---

## Alert Timing

### Best Practices

1. **Email** — Daily digest or instant on deal
2. **SMS** — Only for best deals (save money on SMS)
3. **Slack** — Team channel, all deals
4. **Discord** — Community/personal server, all deals
5. **Predictions** — Background analysis, no interruption

### Rate Limiting

Don't spam! Recommended limits:

- Email: Max 5 per day per user
- SMS: Max 2 per day (costs money!)
- Slack: Max 10 per day
- Discord: Unlimited

---

## Database Integration

All alerts logged in `alerts` table:

```python
from models import Alert, db

# Create alert record
alert = Alert(
    airline='United, Air Canada',
    price=112000,  # cents
    threshold=120000,  # cents
    status='triggered',
    email_sent=True,
    sms_sent=False,
    slack_sent=True,
    discord_sent=False
)

db.session.add(alert)
db.session.commit()

# Query alerts
recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10)
```

---

## Configuration Checklist

- [ ] Email: SMTP credentials set
- [ ] SMS: Twilio account created & configured
- [ ] Slack: Webhook URL added
- [ ] Discord: Webhook URL added
- [ ] Price Threshold: Set in `.env` or database
- [ ] User Preferences: Email, phone, webhooks saved
- [ ] Test: Send test alert to each channel

---

## Troubleshooting

### Email not sending

```bash
# Test SMTP connection
python3 -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
# Should not error
```

### SMS not arriving

- Verify phone number in E.164 format: `+1234567890`
- Check Twilio balance (free trial)
- Verify phone is in supported countries

### Slack/Discord webhooks not working

- Test URL directly:
  ```bash
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test"}' \
    YOUR_WEBHOOK_URL
  ```
- Verify webhook is still active (webhooks expire)

### Prediction accuracy low

- Need at least 30 days of price data
- Linear model works best for trending prices
- Consider upgrading to ML model (future feature)

---

## Upgrading Notification Channels

Want more features? Consider:

- **Telegram** — Bot API, instant messages
- **WhatsApp** — Twilio integration
- **Push Notifications** — Mobile app
- **Apple Watch** — Native alerts
- **Voice Calls** — Twilio Voice

---

## Privacy & Security

- **Email**: Messages sent unencrypted (use HTTPS)
- **SMS**: Encrypted in transit (Twilio handles)
- **Slack/Discord**: HTTPS webhooks, no data at rest
- **Database**: Encrypt sensitive fields (future)

Never commit credentials to Git!

```bash
# .gitignore
.env
.env.local
secrets/
```

---

Need help? Open an issue or check [CONTRIBUTING.md](../CONTRIBUTING.md)
