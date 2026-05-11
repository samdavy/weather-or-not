"""
weather_agent.py — fetches weather and sends a plain report to Telegram.
Requires env vars: BOT_TOKEN, CHAT_ID
Optional: LAT, LON, LOCATION_NAME (defaults to Draper, UT)
"""

import json
import os
import random
import sys
import httpx

# ── Config ────────────────────────────────────────────────────────────────────

BOT_TOKEN        = os.environ["BOT_TOKEN"]
CHAT_ID          = os.environ["CHAT_ID"]
LAT              = os.environ.get("LAT", "40.5247")
LON              = os.environ.get("LON", "-111.8638")
FICTION_DB_PATH  = os.path.join(os.path.dirname(__file__), "fiction.json")


def load_fictional_db(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


FICTION_DB = load_fictional_db(FICTION_DB_PATH)


def get_viable_clothing(temp_f: float, condition: str) -> str:
    condition = condition.lower()
    if "snow" in condition or temp_f <= 32:
        return "Winter coat, insulated boots, gloves, warm hat"
    if "thunderstorm" in condition or "hail" in condition:
        return "Waterproof shell, sturdy shoes, quick-dry layers"
    if "rain" in condition or "drizzle" in condition or "showers" in condition:
        return "Rain jacket, waterproof shoes, layered top"
    if "fog" in condition or "mist" in condition:
        return "Light jacket, long sleeves, non-slip shoes"
    if temp_f <= 45:
        return "Warm jacket, sweater, jeans, closed shoes"
    if temp_f <= 55:
        return "Jacket, long-sleeve shirt, layered top"
    if temp_f <= 65:
        return "Light jacket or hoodie, tee, pants"
    if temp_f <= 75:
        return "Long-sleeve shirt or light tee, pants"
    if temp_f <= 85:
        return "Short-sleeve shirt, shorts or light pants"
    return "Shorts, breathable tee, sun protection"


def get_fictional_analog(weather_code: int) -> str:
    code_key = str(weather_code)
    entry = FICTION_DB.get(code_key)

    if not entry or not isinstance(entry, dict):
        return "Earth"

    settings = entry.get("settings")
    if not settings:
        return entry.get("label", "Earth")

    choice = random.choice(settings)
    return choice.get("setting", entry.get("label", "Earth"))

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
        f"&current=temperature_2m,weathercode,relativehumidity_2m"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&temperature_unit=fahrenheit&windspeed_unit=mph&timezone=auto"
        f"&forecast_days=1"
    )
    r = httpx.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def format_weather_report(data: dict) -> str:
    c = data["current"]
    d = data["daily"]
    code = c.get("weathercode", 0)
    condition = WMO_CODES.get(code, f"code {code}")
    return (
        f"Current Temperature: {round(c['temperature_2m'])}°F\n"
        f"Current Humidity: {round(c['relativehumidity_2m'])}%\n"
        f"Conditions: {condition.title()}\n"
        f"Day High: {round(d['temperature_2m_max'][0])}°F\n"
        f"Day Low: {round(d['temperature_2m_min'][0])}°F\n"
        f"Viable Clothing: {get_viable_clothing(c['temperature_2m'], condition)}\n"
        f"Fictional Analog: {get_fictional_analog(code)}"
    )

# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram(text: str, chat_id: str | None = None) -> None:
    target_chat_id = chat_id or CHAT_ID
    r = httpx.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": target_chat_id, "text": text},
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

    weather_text = format_weather_report(weather_data)
    print("Weather data:\n" + weather_text)
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
