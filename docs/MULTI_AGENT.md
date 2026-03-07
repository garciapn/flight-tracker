# Multi-Agent Architecture

Flight Tracker uses **OpenClaw's multi-agent system** to coordinate independent agents that each handle specific tasks and send real-time updates to Telegram.

---

## Overview

### Main Coordinator (Gerald)
- Orchestrates all sub-agents
- Sends status summaries
- Handles errors and retries
- Runs on schedule (8 AM & 8 PM PST)

### Sub-Agents (Independent Sessions)

Each agent:
- Runs in **isolated session** (own memory, own Telegram access)
- Executes **specific task** (collect, analyze, alert, monitor, predict)
- Sends **real-time updates to Telegram**
- **Works in parallel** (non-blocking)
- Can **spawn child agents** (multi-level coordination)

---

## Architecture

```
Coordinator (Main Session)
    │
    ├─► Collector Agent (Session 1)
    │   ├─ Runs: python3 collect-data.py
    │   ├─ Stores: flights, collections data
    │   └─ Telegram: "✅ Collected 28 flights"
    │
    ├─► Analyzer Agent (Session 2)
    │   ├─ Analyzes: price trends, predictions
    │   ├─ Stores: price_history, predictions
    │   └─ Telegram: "📉 Trend: Dropping 3%"
    │
    ├─► Alert Agent (Session 3)
    │   ├─ Checks: thresholds, deals
    │   ├─ Sends: Email, SMS, Slack, Discord, Telegram
    │   └─ Telegram: "✈️ DEAL FOUND: $1120"
    │
    ├─► Monitor Agent (Session 4)
    │   ├─ Checks: API health, data quality
    │   ├─ Validates: prices, endpoints, webhooks
    │   └─ Telegram: "✅ System healthy"
    │
    └─► Predictor Agent (Session 5)
        ├─ Runs: ML price prediction
        ├─ Predicts: 7 days ahead
        └─ Telegram: "🔮 Book by March 15"
```

---

## Telegram Integration

### Each Agent Can Send Messages

```python
from message import message

# Any agent can send to Telegram channel
message.send(
    target='flight-tracker-channel',
    channel='telegram',
    message='✅ Data collection complete: 28 flights'
)
```

### Example Message Flow

```
08:00 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Collector: "📊 Data collection started..."
  Collector: "🔄 Authenticating with Amadeus..."
  Collector: "✅ Collected 28 flights from Amadeus"
  Collector: "📝 Saved to database"

08:03 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Analyzer: "📈 Analyzing 28 flights..."
  Analyzer: "📊 Price range: $1,120 - $1,400"
  Analyzer: "📉 Trend: Dropping 3% from yesterday"
  Analyzer: "💡 Recommendation: Book by March 15"

08:05 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Alerter: "🚨 Price alert check..."
  Alerter: "✈️ DEAL FOUND!"
  Alerter: "  Airline: United, Air Canada"
  Alerter: "  Price: $1,120/person"
  Alerter: "  Your threshold: $1,200"
  Alerter: "  💰 Save: $80"
  Alerter: "📧 Email sent | 📱 SMS queued | 💬 Slack posted"

08:07 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Monitor: "✅ System Health Check"
  Monitor: "  • Flask API: responding ✅"
  Monitor: "  • Database: connected ✅"
  Monitor: "  • Amadeus API: authorized ✅"
  Monitor: "  • Last collection: 8:00 AM ✅"
  Monitor: "  • Data quality: 28 flights ✅"

08:10 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Predictor: "🔮 7-Day Price Predictions"
  Predictor: "  United, Air Canada:"
  Predictor: "    Current: $1,120"
  Predictor: "    Predicted: $1,095"
  Predictor: "    Trend: Dropping ↓"
  Predictor: "    Confidence: 87%"

08:12 AM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Gerald (Coordinator): "✅ Data collection cycle complete"
  Gerald: "  • 1 deal found"
  Gerald: "  • All systems healthy"
  Gerald: "  • Next run: 8 PM"
```

---

## Use Cases

### 1. Data Collection
**Collector Agent:**
- Runs on schedule (8 AM & 8 PM)
- Collects flights from Amadeus
- Validates data
- Stores in database
- Reports via Telegram

**Telegram Updates:**
```
📊 Collection started...
✅ 28 flights collected
⚠️ API took 15 seconds (normal)
💾 Saved successfully
```

### 2. Price Analysis
**Analyzer Agent:**
- Analyzes historical trends
- Detects patterns
- Runs ML prediction
- Generates recommendations

**Telegram Updates:**
```
📈 Analysis Results
  Price range: $1,120-$1,400
  Average: $1,150
  Trend: Dropping 3% this week
  Best booking day: March 15
  Confidence: High
```

### 3. Deal Detection
**Alert Agent:**
- Monitors price threshold
- Sends multi-channel alerts
- Tracks alert history
- Logs results

**Telegram Updates:**
```
✈️ DEAL ALERT!
Airline: United, Air Canada
Price: $1,120/person
Threshold: $1,200/person
SAVE: $80! 

📧 Email sent to paolo@example.com
📱 SMS sent to +1 (555) 123-4567
💬 Slack posted
🎮 Discord posted
```

### 4. System Monitoring
**Monitor Agent:**
- Checks API health
- Validates databases
- Tests webhooks
- Monitors performance

**Telegram Updates:**
```
✅ System Health Report
  API: responding (123ms)
  Database: 28 flights stored
  Amadeus: authorized
  Webhooks: 4/4 active
  Last collection: 8:00 AM
  Next: 8 PM
```

### 5. ML Predictions
**Predictor Agent:**
- Forecasts prices
- Calculates trends
- Advises booking times
- Updates confidence

**Telegram Updates:**
```
🔮 Price Forecast (7 days)
  Current: $1,120
  Predicted: $1,095
  Trend: Dropping ↓
  Confidence: 87%
  Recommendation: WAIT (save more)
```

---

## Running Agents

### Option 1: Manual Coordinator

```bash
python3 coordinator.py
```

Spawns all agents and prints example flow.

### Option 2: Automated (8 AM & 8 PM)

The launchd scheduler runs:
```bash
bash run-collection-with-amadeus.sh
```

Which internally:
1. Spawns Collector Agent
2. Waits for completion
3. Spawns Analyzer Agent
4. Spawns Alert Agent
5. Spawns Monitor Agent
6. Spawns Predictor Agent
7. Sends Coordinator summary

### Option 3: On-Demand

```python
from sessions_spawn import sessions_spawn

# Spawn specific agent
sessions_spawn(
    task='Check for price deals and alert',
    label='Alert Agent',
    mode='run'
)
```

---

## Agent Communication

### Telegram Channel
All agents send to **single Telegram channel** for unified feed:
```env
TELEGRAM_TRACKER_CHANNEL=@flight_tracker_channel
```

Or split by agent:
```env
TELEGRAM_COLLECTOR_CHANNEL=@ft_collector
TELEGRAM_ANALYZER_CHANNEL=@ft_analyzer
TELEGRAM_ALERTER_CHANNEL=@ft_alerter
```

### Inter-Agent Messages

Agents can send messages to each other:

```python
# Analyzer queries Collector for latest data
sessions_send(
    sessionKey='collector_session',
    message='What was the last collection timestamp?'
)
```

### Agent → Coordinator

Sub-agents report back:
```python
message.send(
    target='coordinator_channel',
    message='Collection complete: 28 flights, 5 alerts'
)
```

---

## Error Handling

### Agent Failures

If an agent fails:

1. **Monitor Agent detects it** (detects missing update)
2. **Sends Telegram alert**:
   ```
   ⚠️ Collector Agent failed
   Last update: 8:00 AM
   Error: API timeout
   Retrying in 5 minutes...
   ```
3. **Coordinator retries** (exponential backoff)
4. **Routes around failure** (use cached data)

### Example Failure Flow

```
08:00 - Collector starts
08:03 - Collector fails (API timeout)
        "❌ Amadeus API timeout"
08:04 - Monitor detects (no new flights)
        "⚠️ Collection agent unresponsive"
08:05 - Coordinator retries
        "🔄 Retrying collection..."
08:08 - Collector succeeds
        "✅ Collected 28 flights (retry)"
```

---

## Scaling

### Add New Agents

1. Create agent task in `coordinator.py`
2. Define Telegram message format
3. Spawn in `start_all_agents()`
4. Agent auto-sends updates

### Example: Email Summary Agent

```python
def spawn_email_summary_agent(self):
    agent_config = {
        'task': '''
        Generate and send daily email summary:
        - Best prices
        - Deals found
        - Trend analysis
        - Booking recommendations
        
        Send to Paolo's email.
        ''',
        'label': 'Email Summarizer',
        'mode': 'session'
    }
    return agent_config
```

### Parallel Execution

All agents run **in parallel** after Collector finishes:

```
Timeline:
08:00 - Collector ████████ (3 min)
08:03 - Analyzer    ███ (1 min)    │
        Alerter     ███ (1 min)    ├─ All parallel
        Monitor     ██  (30 sec)   │
        Predictor   ███ (1 min)    │
08:05 - Done (5 min total instead of 8 min sequential)
```

---

## Configuration

### Enable/Disable Agents

```env
AGENT_COLLECTOR_ENABLED=true
AGENT_ANALYZER_ENABLED=true
AGENT_ALERTER_ENABLED=true
AGENT_MONITOR_ENABLED=true
AGENT_PREDICTOR_ENABLED=true

# Telegram
TELEGRAM_TRACKER_CHANNEL=@flight_tracker_channel
TELEGRAM_SEND_UPDATES=true
```

### Per-Agent Config

```env
# Collector
COLLECTOR_TIMEOUT=30
COLLECTOR_RETRY_COUNT=3

# Analyzer
ANALYZER_MIN_DATA_POINTS=7
ANALYZER_PREDICTION_DAYS=7

# Alerter
ALERTER_CHANNELS=email,sms,slack,discord,telegram
ALERTER_BATCH_SIZE=10

# Monitor
MONITOR_CHECK_INTERVAL=300
MONITOR_ALERT_ON_FAILURE=true

# Predictor
PREDICTOR_MODEL=linear_regression
PREDICTOR_MIN_CONFIDENCE=0.7
```

---

## Monitoring Agents

### View Agent Status

```python
from subagents import subagents

# List all running agents
subagents(action='list')

# Kill specific agent
subagents(action='kill', target='collector')

# Send message to agent
subagents(action='steer', target='analyzer', message='Run analysis now')
```

### Example Output

```
Active Sub-Agents:
  1. Collector (Session: coll-abc123)
     Status: running
     Uptime: 2 minutes
     Last message: "✅ Collected 28 flights"
  
  2. Analyzer (Session: anal-def456)
     Status: running
     Uptime: 1 minute
     Last message: "📉 Trend: Dropping 3%"
  
  3. Alerter (Session: alrt-ghi789)
     Status: idle (waiting for threshold)
     Uptime: 5 minutes
  
  4. Monitor (Session: mntr-jkl012)
     Status: running
     Uptime: 3 minutes
     Last message: "✅ System healthy"
  
  5. Predictor (Session: pred-mno345)
     Status: running
     Uptime: 1 minute
     Last message: "🔮 Predictions updated"
```

---

## Benefits

✅ **Real-time updates** — Telegram feed shows everything happening  
✅ **Parallel execution** — All agents run simultaneously  
✅ **Resilience** — One agent failure doesn't block others  
✅ **Scalability** — Add agents without changing core  
✅ **Isolation** — Each agent has clean session/memory  
✅ **Observability** — Full audit trail in Telegram  
✅ **Control** — Coordinator can steer/pause agents  

---

## Example: Full Workflow

```
Schedule: 8 AM PST
↓
Coordinator spawns agents:
  Collector → "📊 Starting collection..."
  
Collector (5 seconds):
  → "🔄 Authenticating Amadeus..."
  → "✅ Got 28 flights"
  → "💾 Database saved"

Analyzer (spawned after Collector finishes):
  → "📈 Analyzing trends..."
  → "📉 Dropping 3% this week"
  → "💡 Book by March 15"

Alerter (parallel with Analyzer):
  → "🚨 Checking deals..."
  → "✈️ FOUND: $1120 < $1200"
  → "📧📱💬🎮 Alerts sent"

Monitor (parallel):
  → "✅ Health: All systems green"

Predictor (parallel):
  → "🔮 7-day forecast updated"
  → "Confidence: 87%"

Coordinator (final):
  → "✅ Complete in 2 minutes"
  → "📊 1 deal found, all systems healthy"
  → "⏰ Next run: 8 PM"

Result: Paolo gets real-time Telegram feed of everything!
```

---

## What's Next?

- [ ] Multi-level agent spawning (agents spawn child agents)
- [ ] Agent voting (multiple agents vote on threshold)
- [ ] Cross-agent learning (analyzer teaches predictor)
- [ ] Performance optimization (parallel batch processing)
- [ ] Advanced error recovery (agent auto-healing)

---

Questions? Check [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue!
