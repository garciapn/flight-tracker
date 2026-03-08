# Jamal Bot Setup - Complete Guide

Create a **separate Telegram bot for Jamal** so he operates independently from Gerald.

---

## Quick Overview

**Before:**
```
One bot (Gerald)
├─ Flight Tracker updates
├─ Jamal crypto updates
└─ All mixed together ❌
```

**After:**
```
Two bots (separate)
├─ Bot 1: Gerald (Flight Tracker)
│  └─ @flight_tracker_updates
│
└─ Bot 2: Jamal (Crypto Mining) ← NEW
   └─ @jamal_crypto_mining
```

Clean separation! ✅

---

## Step 1: Create Jamal's Telegram Bot

### Via @BotFather (5 minutes)

**1. Open Telegram**

**2. Search for `@BotFather`** (official Telegram bot manager)

**3. Send:** `/newbot`

**4. Answer the prompts:**

```
BotFather: What should your bot be called?
You: Jamal Crypto Miner

BotFather: Give your bot a username.
You: jamal_crypto_mining_bot
(Must end with "_bot", must be unique)
```

**5. BotFather gives you:**

```
Done! Congratulations on your new bot. 
You will find it at https://t.me/jamal_crypto_mining_bot. 

Use this token to access the HTTP API:
123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg

Keep your token secure and store it safely!
```

**Copy that token!** You'll need it in .env

---

## Step 2: Configure Jamal in Your Code

### Update `.env`

```env
# Gerald's bot (Flight Tracker)
TELEGRAM_BOT_TOKEN=your_gerald_token_here
TELEGRAM_TRACKER_CHANNEL=@flight_tracker_updates

# Jamal's bot (SEPARATE - Crypto Mining)
JAMAL_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg
JAMAL_TELEGRAM_CHANNEL=@jamal_crypto_mining

# Multi-agent settings
ENABLE_JAMAL_AGENT=true
```

**Never commit these tokens!** `.gitignore` protects them.

---

## Step 3: Create Jamal's Channel (Optional but Recommended)

### Why a channel?
- Organized feed
- Easy to find updates
- Professional setup
- Can invite others to watch

### Create channel:

**In Telegram:**
1. **Tap:** Menu → New Channel
2. **Channel name:** `Jamal Crypto Mining`
3. **Description:** `Real-time cryptocurrency mining research, analysis, and operations. Powered by Jamal AI.`
4. **Privacy:** Public or Private (your choice)
5. **Username:** `jamal_crypto_mining` (matches bot username)
6. **Add Jamal bot as admin:** Settings → Admins → Add jamal_crypto_mining_bot

Now Jamal can post directly to this channel!

---

## Step 4: Test the Setup

### Run Jamal initialization:

```bash
python3 jamal_crypto_miner.py
```

Output:
```
============================================================
🚀 JAMAL CRYPTO MINING AGENT INITIALIZATION
============================================================

🚀 JAMAL HAS ARRIVED 🚀

Yo, I'm JAMAL - Your Crypto Mining Master Agent
...
```

### Check Telegram:

**You should see:**
1. @jamal_crypto_mining_bot is live
2. Channel @jamal_crypto_mining exists
3. Bot can post messages

---

## Step 5: Spawn Jamal Agent

### Python code to spawn:

```python
from sessions_spawn import sessions_spawn
from jamal_crypto_miner import JamalCryptoMiner

jamal = JamalCryptoMiner()

# Spawn as persistent sub-agent
sessions_spawn(**jamal.spawn_jamal())
```

**Result:**
- Jamal spawns with his own bot token
- Posts to his own channel (@jamal_crypto_mining)
- Completely independent from Gerald
- You can chat with Jamal directly

---

## Telegram Structure

### Gerald's setup:

```
@flight_tracker_updates (Channel)
    ↑
    │ Posts via
    │
flight-tracker-bot
    ↑
    │ Token:
    │
TELEGRAM_BOT_TOKEN=xxx_gerald_xxx
```

### Jamal's setup:

```
@jamal_crypto_mining (Channel)
    ↑
    │ Posts via
    │
jamal_crypto_mining_bot
    ↑
    │ Token:
    │
JAMAL_BOT_TOKEN=xxx_jamal_xxx
```

**Two separate systems!**

---

## Managing Channels

### Check all your bots:

In Telegram, go to **Settings → Bots** to see:
- ✅ flight-tracker-bot
- ✅ jamal_crypto_mining_bot

### Mute/Unmute notifications:

Each channel can have separate notification settings. Mute Jamal if you want crypto updates later!

### Archive channels:

Swipe left on channel to hide without deleting.

---

## Private vs Public

### Public Channel (`@jamal_crypto_mining`)
```
Pros:
  ✅ Anyone can follow
  ✅ Share analysis publicly
  ✅ Build audience
  ✅ Professional portfolio

Cons:
  ❌ Your data is visible
  ❌ Others see your mining setup
```

### Private Channel
```
Pros:
  ✅ Only you see updates
  ✅ Keep strategy private
  ✅ Still get Telegram notifications

Cons:
  ❌ Must invite people manually
  ❌ No public portfolio value
```

**Recommendation:** Public for now (great for GitHub portfolio!), switch private if needed.

---

## Telegram API (Optional Advanced)

### Send messages programmatically:

```python
import requests

def send_jamal_message(message):
    url = f"https://api.telegram.org/bot{JAMAL_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": "@jamal_crypto_mining",
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# Example:
send_jamal_message("⛏️ Bitcoin analysis complete! ROI: 12 months")
```

---

## Troubleshooting

### Bot doesn't send messages?

**Check:**
1. Is JAMAL_BOT_TOKEN set correctly?
2. Does channel @jamal_crypto_mining exist?
3. Is bot added as admin?
4. Did you make channel public?

### Can't find bot?

Search for: `@jamal_crypto_mining_bot`

### Token invalid?

Go back to @BotFather, send `/token jamal_crypto_mining_bot`

### Wrong channel?

Create channel with exact username: `jamal_crypto_mining`

---

## Environment Checklist

```env
✅ JAMAL_BOT_TOKEN=123456789:ABCD...
✅ JAMAL_TELEGRAM_CHANNEL=@jamal_crypto_mining
✅ ENABLE_JAMAL_AGENT=true
✅ TELEGRAM_BOT_TOKEN=xxx (Gerald's token, separate)
✅ TELEGRAM_TRACKER_CHANNEL=@flight_tracker_updates
```

---

## Final Result

You now have:

```
Telegram

Flight Tracker Channel
  📊 "✅ 28 flights collected"
  📊 "📉 Prices dropping 3%"

Jamal Crypto Mining Channel  
  ⛏️ "Bitcoin ASIC analysis complete"
  ⛏️ "Monero CPU mining: $2-5/day"
```

**Two independent bots, two separate channels, zero confusion!** ✅

---

## Next Steps

1. ✅ Create bot via @BotFather
2. ✅ Add token to .env
3. ✅ Create @jamal_crypto_mining channel
4. ✅ Add bot as admin
5. ✅ Run `python3 jamal_crypto_miner.py`
6. ✅ Spawn Jamal agent
7. ✅ Watch Telegram! 🚀

---

**Questions?** Check [JAMAL_CRYPTO.md](./JAMAL_CRYPTO.md) or [CONTRIBUTING.md](../CONTRIBUTING.md)

**Let's go! ⛏️💰**
