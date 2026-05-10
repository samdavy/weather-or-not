"""
bot_server.py — listens for Telegram messages, responds with weather on demand.
Send any message to your bot to trigger a weather report.
Requires same env vars as weather_agent.py + PORT (set automatically by Railway).
"""

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from weather_agent import get_weather, format_weather_for_llm, ask_claude, send_telegram

PORT = int(os.environ.get("PORT", 8080))


def handle_update(update: dict) -> None:
    """Process a single Telegram update."""
    try:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "").strip().lower()
    except KeyError:
        return  # not a text message, ignore

    # any message triggers a report
    try:
        weather_data = get_weather()
        weather_text = format_weather_for_llm(weather_data)
        message = ask_claude(weather_text)
    except Exception as e:
        message = f"something broke: {e}"

    try:
        import httpx
        httpx.post(
            f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as e:
        print(f"Failed to reply: {e}")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        # respond to Telegram immediately, process in background
        self.send_response(200)
        self.end_headers()
        threading.Thread(target=handle_update, args=(update,), daemon=True).start()

    def do_GET(self):
        # health check endpoint — Railway uses this to confirm the service is up
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"Listening on port {PORT}")
    server.serve_forever()
