# Deployment Guide

Deploy Flight Tracker to production.

## Platforms

- [Heroku](#heroku) — Easy, free tier available
- [Railway](#railway) — Modern, simple deployment
- [PythonAnywhere](#pythonanywhere) — Python-specific hosting
- [AWS](#aws) — Scalable, production-grade
- [DigitalOcean](#digitalocean) — Affordable VPS
- [Docker + Kubernetes](#docker--kubernetes) — Enterprise

## Heroku Deployment

### Step 1: Install Heroku CLI

```bash
brew install heroku
heroku login
```

### Step 2: Create Heroku App

```bash
heroku create flight-tracker-yourname
```

### Step 3: Add Procfile

Create `Procfile` in project root:

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

### Step 4: Set Environment Variables

```bash
heroku config:set AMADEUS_CLIENT_ID=your_client_id
heroku config:set AMADEUS_CLIENT_SECRET=your_client_secret
heroku config:set EMAIL_SENDER=your_email@gmail.com
heroku config:set EMAIL_PASSWORD=your_app_password
```

### Step 5: Deploy

```bash
git push heroku main
```

### Step 6: View Logs

```bash
heroku logs --tail
```

Your app is now live at: `https://flight-tracker-yourname.herokuapp.com`

---

## Railway Deployment

### Step 1: Connect Repository

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select `flight-tracker` repository

### Step 2: Set Environment Variables

In Railway dashboard:
- Go to "Variables"
- Add `AMADEUS_CLIENT_ID`
- Add `AMADEUS_CLIENT_SECRET`
- Add `EMAIL_SENDER` (optional)
- Add `EMAIL_PASSWORD` (optional)

### Step 3: Configure Start Command

Add `Procfile`:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

Railway auto-deploys on `git push`!

---

## PythonAnywhere Deployment

### Step 1: Create Account

Go to https://www.pythonanywhere.com and sign up (free tier available).

### Step 2: Clone Repository

In PythonAnywhere bash console:
```bash
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker
```

### Step 3: Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.9 flighttracker
pip install -r requirements.txt
pip install gunicorn
```

### Step 4: Configure Web App

1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.9
5. Set source code to `/home/username/flight-tracker`

### Step 5: Configure WSGI

Edit the WSGI file to:
```python
import sys
path = '/home/username/flight-tracker'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

### Step 6: Set Environment Variables

Add to `~/.bashrc`:
```bash
export AMADEUS_CLIENT_ID=your_client_id
export AMADEUS_CLIENT_SECRET=your_client_secret
```

Reload: `source ~/.bashrc`

Your app is live!

---

## AWS Deployment

### Option A: Elastic Beanstalk (Easiest)

```bash
# Install EB CLI
brew install aws-elasticbeanstalk/tap/aws-eb

# Initialize
eb init -p python-3.9 flight-tracker --region us-west-2

# Create environment
eb create production

# Deploy
git push
```

### Option B: EC2 + Gunicorn

1. Launch EC2 instance (Ubuntu 20.04)
2. SSH in
3. Install Python & dependencies:

```bash
sudo apt update
sudo apt install python3.9 python3-pip nginx
pip3 install gunicorn flask requests

# Clone repo
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker
pip install -r requirements.txt
```

4. Create systemd service (`/etc/systemd/system/flighttracker.service`):

```ini
[Unit]
Description=Flight Tracker
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/flight-tracker
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

5. Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl start flighttracker
sudo systemctl enable flighttracker
```

---

## DigitalOcean Deployment

### Step 1: Create Droplet

1. Create Ubuntu 20.04 droplet
2. SSH in

### Step 2: Install Dependencies

```bash
sudo apt update
sudo apt install python3.9 python3-pip nginx supervisor git

pip3 install --upgrade pip
pip3 install gunicorn flask requests python-dotenv
```

### Step 3: Clone & Setup

```bash
git clone https://github.com/garciapn/flight-tracker.git
cd flight-tracker
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Step 4: Configure Supervisor

Create `/etc/supervisor/conf.d/flighttracker.conf`:

```ini
[program:flighttracker]
directory=/home/ubuntu/flight-tracker
command=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
```

### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/flighttracker`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/flighttracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flighttracker
```

---

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3737", "app:app"]
```

### Build & Run

```bash
docker build -t flight-tracker .
docker run -p 3737:3737 \
  -e AMADEUS_CLIENT_ID=your_id \
  -e AMADEUS_CLIENT_SECRET=your_secret \
  flight-tracker
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "3737:3737"
    environment:
      - AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID}
      - AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET}
      - EMAIL_SENDER=${EMAIL_SENDER}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
```

Run:
```bash
docker-compose up
```

---

## GitHub Pages (Docs Only)

Deploy documentation to GitHub Pages:

1. Create `docs/` branch
2. Enable GitHub Pages in Settings
3. Select `/docs` folder as source
4. Documentation is now at `https://garciapn.github.io/flight-tracker`

---

## Performance Tips

### Database

For production, upgrade to a real database:

```bash
pip install sqlite3  # Built-in, simple
# OR
pip install psycopg2  # PostgreSQL
```

### Caching

Add caching for API responses:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/flights')
@cache.cached(timeout=300)  # Cache for 5 minutes
def flights():
    ...
```

### Monitoring

Use tools like:
- **Sentry** — Error tracking
- **DataDog** — Performance monitoring
- **New Relic** — APM

---

## SSL/HTTPS

### Let's Encrypt (Free)

```bash
sudo certbot certonly --nginx -d your-domain.com
```

### AWS Certificate Manager

Free SSL for AWS resources.

---

## Auto-scaling

Set up automated data collection:

- **GitHub Actions** — Runs scheduled jobs
- **Cloud Scheduler** — GCP scheduled tasks
- **EventBridge** — AWS scheduled events

---

## Monitoring & Alerting

1. **Uptime monitoring** — UptimeRobot, Pingdom
2. **Error tracking** — Sentry
3. **Performance** — New Relic, DataDog
4. **Cost tracking** — CloudZero

---

## Backup & Recovery

- Regular database backups
- Git history as backup
- Disaster recovery plan

---

## Scaling Checklist

- [ ] Database indexed
- [ ] Caching enabled
- [ ] CDN configured
- [ ] Rate limiting set
- [ ] Monitoring active
- [ ] Backups automated
- [ ] Load balancing ready

---

Happy deploying! 🚀
