# weather-agent

Sends AI-editorializied weather reports to Telegram 3x/day via GitHub Actions.

## Setup

### 1. Telegram bot

1. Message `@BotFather` on Telegram → `/newbot` → follow prompts → copy the token
2. Message your new bot once (so it has a chat to send to)
3. Get your chat ID:
   ```
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"chat": {"id": 123456789}` in the response

### 2. Get your coordinates

Find lat/lon for your location: https://www.latlong.net/

### 3. GitHub repo secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret | Value |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token |
| `CHAT_ID` | Your Telegram chat ID (the number) |
| `OPENROUTER_API_KEY` | Your OpenRouter API key (openrouter.ai/keys) |

LAT/LON/LOCATION_NAME are hardcoded to Draper, UT — override with secrets if needed.

### 4. Push to GitHub

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/YOU/weather-agent.git
git push -u origin main
```

The workflow will run automatically at 8 AM, 1 PM, and 6 PM UTC.
Trigger it manually anytime via Actions → Weather Agent → Run workflow.

## Adjusting the schedule

Edit `.github/workflows/weather.yml`. Cron times are in UTC.
Converter: https://dateful.com/time-zone-converter

## Adjusting the personality

Edit the `SYSTEM_PROMPT` in `weather_agent.py`. Current vibe: terse, world-weary, dry.

## Running locally

```bash
export BOT_TOKEN=...
export CHAT_ID=...
export OPENROUTER_API_KEY=...
# optional overrides — defaults to Draper, UT
# export LAT=40.5247
# export LON=-111.8638
# export LOCATION_NAME="Draper, UT"

pip install httpx
python weather_agent.py
```
