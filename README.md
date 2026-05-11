# weather-or-not

Sends a plain weather report to Telegram. Two modes:

- **On-demand:** message the bot, get a current report back (Telegram webhook, runs as a Railway web service).
- **Scheduled:** 3x/day automatic push to a fixed chat (Railway cron service).

## Setup

### 1. Create a Telegram bot

1. Message `@BotFather` on Telegram → `/newbot` → follow prompts → copy the token.
2. Message your new bot once (so it has a chat to send to).
3. Get your chat ID:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"chat": {"id": 123456789}` in the response.

### 2. Get your coordinates

Find lat/lon for your location: https://www.latlong.net/ (defaults are Draper, UT).

### 3. Deploy to Railway

Create a new Railway project from this repo. You'll add **two services** to the same project, both pointing at the same repo. They'll share env vars at the project level.

**Project-level env vars** (set once, shared by both services):

| Variable    | Value                          |
|-------------|--------------------------------|
| `BOT_TOKEN` | Your Telegram bot token        |
| `CHAT_ID`   | Your Telegram chat ID (number) |
| `LAT`       | (optional) latitude override   |
| `LON`       | (optional) longitude override  |

#### Service A — webhook (on-demand replies)

- Type: **Web service**
- Start command: leave default (uses `Procfile`: `python bot_server.py`)
- After it deploys, grab the public URL (e.g. `https://weather-or-not.up.railway.app`) and register the webhook with Telegram:
  ```bash
  curl -F "url=https://<your-app>.up.railway.app/webhook" \
       https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
  ```

#### Service B — scheduled push (3x/day report)

- Type: **Cron service** (Railway → New Service → from same repo → set service type to Cron)
- Start command override: `python weather_agent.py`
- Cron schedule (UTC; times below are MST / winter — they'll be one hour later in clock time during DST):
  - `0 15 * * *` — 8 AM Mountain
  - `0 20 * * *` — 1 PM Mountain
  - `0 1 * * *` — 6 PM Mountain
  
  Railway cron services run a single schedule per service, so either set up three cron services or pick the one that matters most. Cron syntax converter: https://crontab.guru/

## Running locally

```bash
export BOT_TOKEN=...
export CHAT_ID=...
# optional overrides — defaults to Draper, UT
# export LAT=40.5247
# export LON=-111.8638

pip install -r requirements.txt
python weather_agent.py    # one-shot scheduled-report behavior
# or
python bot_server.py       # webhook server on $PORT (default 8080)
```

## Behavior

The script sends a plain, formatted weather report without AI editorialization.
