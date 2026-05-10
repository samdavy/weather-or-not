"""
weather_agent.py — fetches weather, asks Claude to editorialize, sends to Telegram.
Requires env vars: BOT_TOKEN, CHAT_ID, OPENROUTER_API_KEY
Optional: LAT, LON, LOCATION_NAME (defaults to Draper, UT)
"""

import os
import sys
import httpx

# ── Config ────────────────────────────────────────────────────────────────────

BOT_TOKEN        = os.environ["BOT_TOKEN"]
CHAT_ID          = os.environ["CHAT_ID"]
OPENROUTER_KEY   = os.environ["OPENROUTER_API_KEY"]
LAT              = os.environ.get("LAT", "40.5247")
LON              = os.environ.get("LON", "-111.8638")
LOCATION         = os.environ.get("LOCATION_NAME", "Draper, UT")

MODEL = "anthropic/claude-sonnet-4.6"

SYSTEM_PROMPT = """\
You are a terse, slightly world-weary weather observer. Given current conditions, \
tell the person what to wear today — be specific and practical (jacket, layers, sunscreen, umbrella, etc). \
Lead with the outfit verdict, then one dry observation about the day. \
Two to three sentences max. No emojis unless ironic. Never cheerful in a forced way.\
"""

WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "icy fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "light showers", 81: "showers", 82: "violent showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail",
}

# ── Weather ───────────────────────────────────────────────────────────────────

def get_weather() -> dict:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,apparent_temperature,weathercode,"
        f"windspeed_10m,relativehumidity_2m,precipitation"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_probability_max,precipitation_sum,uv_index_max"
        f"&temperature_unit=fahrenheit&windspeed_unit=mph&timezone=auto"
        f"&forecast_days=1"
    )
    r = httpx.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def format_weather_for_llm(data: dict) -> str:
    c = data["current"]
    d = data["daily"]
    code = c.get("weathercode", 0)
    condition = WMO_CODES.get(code, f"code {code}")
    return (
        f"Location: {LOCATION}\n"
        f"Condition: {condition}\n"
        f"Temperature: {c['temperature_2m']}°F (feels like {c['apparent_temperature']}°F)\n"
        f"Today's range: {d['temperature_2m_min'][0]}°F – {d['temperature_2m_max'][0]}°F\n"
        f"Rain chance: {d['precipitation_probability_max'][0]}%\n"
        f"Precipitation: {d['precipitation_sum'][0]} mm expected today\n"
        f"UV index: {d['uv_index_max'][0]}\n"
        f"Wind: {c['windspeed_10m']} mph\n"
        f"Humidity: {c['relativehumidity_2m']}%"
    )

# ── LLM ───────────────────────────────────────────────────────────────────────

def ask_claude(weather_text: str) -> str:
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 150,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": weather_text},
            ],
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram(text: str) -> None:
    r = httpx.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=10,
    )
    r.raise_for_status()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        weather_data = get_weather()
    except Exception as e:
        print(f"Weather fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    weather_text = format_weather_for_llm(weather_data)
    print("Weather data:\n" + weather_text)

    try:
        message = ask_claude(weather_text)
    except Exception as e:
        print(f"Claude call failed: {e}", file=sys.stderr)
        message = weather_text

    print("Sending:", message)

    try:
        send_telegram(message)
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("Done.")

if __name__ == "__main__":
    main()
