# Installation Guide

Get Flight Tracker running locally in 5 minutes.

## Prerequisites

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **Git** — [Install](https://git-scm.com/)
- **Amadeus API credentials** — [Free sandbox](https://developers.amadeus.com/) (takes 2 minutes)
- **Email credentials** (optional) — For price alerts

## Step 1: Clone the Repository

```bash
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker
```

## Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov  # For running tests
```

## Step 4: Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

### Required: Amadeus API

1. Go to https://developers.amadeus.com/
2. Sign up (free)
3. Create a new app in the sandbox
4. Copy **Client ID** and **Client Secret**
5. Paste into `.env`:

```env
AMADEUS_CLIENT_ID=your_client_id_here
AMADEUS_CLIENT_SECRET=your_client_secret_here
```

### Optional: Email Alerts

To enable price alert emails, add:

```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

**For Gmail:**
1. Enable 2-factor authentication on your account
2. Generate an "App Password" at https://myaccount.google.com/apppasswords
3. Use this password (not your regular password) in `.env`

**For other providers:**
- Outlook: `smtp.outlook.com` port 587
- Yahoo: `smtp.mail.yahoo.com` port 587
- Custom: Check your email provider's SMTP settings

### Optional: Price Threshold

```env
PRICE_THRESHOLD=1200  # Alert when flights drop below this price/person
```

## Step 5: Run the Application

### Option A: Flask Development Server

```bash
python3 app.py
```

Visit http://localhost:3737 in your browser.

### Option B: Production Server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:3737 app:app
```

## Step 6: Data Collection (Optional)

For automated data collection on macOS:

```bash
# Copy the launchd configuration
cp com.flighttracker.collect.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.flighttracker.collect.plist

# Verify it's loaded
launchctl list | grep flighttracker
```

For manual collection:
```bash
python3 collect-data.py
python3 analyze-prices.py
```

## Step 7: Run Tests

```bash
pytest test_tracker.py -v
```

Or with coverage:
```bash
pytest test_tracker.py --cov=. --cov-report=html
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

Make sure you activated your virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### "AMADEUS_CLIENT_ID not found"

Check that `.env` file exists in the project root and contains your credentials:
```bash
cat .env
```

### "Connection refused at localhost:3737"

The Flask server isn't running. In another terminal:
```bash
python3 app.py
```

### "Amadeus API timeout"

This is normal if the API is slow. The system has a fallback that uses cached data.

### Email alerts not sending

Check your email credentials:
- Gmail: Use an app-specific password, not your regular password
- Enable "Less secure app access" for non-Gmail providers
- Check spam folder

### Tests failing

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Next Steps

- **Check the [Usage Guide](USAGE.md)** — Learn how to use the dashboard
- **Read the [API Docs](API.md)** — Integrate with your own apps
- **See [Deployment Guide](DEPLOYMENT.md)** — Deploy to production
- **Explore [Development](DEVELOPMENT.md)** — Contribute features

## Getting Help

- **Issues?** Open a [GitHub issue](https://github.com/garciapn/flight-tracker/issues)
- **Questions?** Check [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Found a bug?** Please report it!

---

Happy tracking! ✈️
